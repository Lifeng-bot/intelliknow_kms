
import logging
from typing import Optional
from botbuilder.core import (
    ActivityHandler,
    TurnContext,
    CardFactory,
    MessageFactory
)
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    Attachment,
    AttachmentLayoutTypes
)
from botbuilder.integration.aiohttp import BotFrameworkAdapter, BotFrameworkAdapterSettings
from app.config import settings
from core.orchestrator import query_orchestrator
from core.response_generator import response_generator

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TeamsBot(ActivityHandler):
    """Microsoft Teams Bot for IntelliKnow KMS"""

    def __init__(self):
        """Initialize the Teams bot."""
        if not settings.TEAMS_APP_ID or not settings.TEAMS_APP_PASSWORD:
            logger.warning("TEAMS_APP_ID or TEAMS_APP_PASSWORD not configured. Teams bot will not be available.")
            self.settings = None
        else:
            self.settings = BotFrameworkAdapterSettings(
                app_id=settings.TEAMS_APP_ID,
                app_password=settings.TEAMS_APP_PASSWORD
            )

        self.adapter = BotFrameworkAdapter(self.settings) if self.settings else None

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming message activities."""
        user_id = turn_context.activity.from_property.id
        user_name = turn_context.activity.from_property.name
        query_text = turn_context.activity.text.strip()

        logger.info(f"Received query from user {user_id} ({user_name}): {query_text}")

        try:
            # Send typing indicator
            await turn_context.send_activities([
                Activity(
                    type=ActivityTypes.typing,
                    text="Searching knowledge base..."
                )
            ])

            # Process the query through the orchestrator
            routing_info = query_orchestrator.route_query(query_text)

            # Generate query embedding
            query_embedding = response_generator.generate_query_embedding(query_text)

            # Get relevant documents
            relevant_docs = response_generator.get_relevant_documents(
                query_embedding=query_embedding,
                intent_id=routing_info["intent_id"] if routing_info["use_intent"] else None
            )

            # Generate response
            response_data = response_generator.generate_response(
                query=query_text,
                retrieved_docs=relevant_docs,
                intent=routing_info["intent"] if routing_info["use_intent"] else None
            )

            # Format the response for Teams
            response_text = self._format_response(
                response=response_data["response"],
                citations=response_data["citations"],
                confidence=response_data["confidence"],
                intent=routing_info["intent"]
            )

            # Send the response
            await turn_context.send_activity(MessageFactory.text(response_text))

            logger.info(f"Response sent to user {user_id} successfully")

        except Exception as e:
            logger.error(f"Error processing query from user {user_id}: {e}")
            await turn_context.send_activity(
                "Sorry, I encountered an error while processing your query. Please try again later."
            )

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        """Handle when members are added to the conversation."""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_message = """
🤖 Welcome to IntelliKnow KMS Bot!

I can help you find information from our knowledge base. Just ask me a question!

**How to use:**
- Simply type your question in natural language
- I'll search the knowledge base and provide relevant information
- You can ask follow-up questions for clarification

**Example questions:**
- What is the company's leave policy?
- How do I submit an expense report?
- What are the working hours?

**Tips:**
- Be specific in your questions
- Use relevant keywords
- Ask one question at a time

Type your question to get started!
                """
                await turn_context.send_activity(MessageFactory.text(welcome_message))

    def _format_response(self, response: str, citations: list, confidence: float, intent: str) -> str:
        """Format the response for Teams."""
        formatted_response = f"**Answer:**\n\n{response}\n\n"

        # Add confidence level
        confidence_emoji = "🔴" if confidence < 0.3 else "🟡" if confidence < 0.7 else "🟢"
        formatted_response += f"{confidence_emoji} **Confidence:** {confidence:.2%}\n"

        # Add intent
        if intent:
            formatted_response += f"📂 **Intent:** {intent}\n"

        # Add citations if available
        if citations:
            formatted_response += "\n**Sources:**\n"
            for i, citation in enumerate(citations, 1):
                title = citation.get("title", f"Document {i}")
                formatted_response += f"{i}. {title}\n"

        return formatted_response

    def _create_help_card(self) -> Attachment:
        """Create a help card for Teams."""
        card = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.2",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "📚 IntelliKnow KMS Bot Help",
                        "size": "Large",
                        "weight": "Bolder"
                    },
                    {
                        "type": "TextBlock",
                        "text": "How to use:",
                        "weight": "Bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "1. Simply type your question in natural language\n2. I'll search the knowledge base and provide relevant information\n3. You can ask follow-up questions for clarification",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "Example questions:",
                        "weight": "Bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "- What is the company's leave policy?\n- How do I submit an expense report?\n- What are the working hours?",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "Tips:",
                        "weight": "Bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "- Be specific in your questions\n- Use relevant keywords\n- Ask one question at a time",
                        "wrap": True
                    }
                ]
            }
        }
        return CardFactory.adaptive_card(card)


# Global Teams bot instance
teams_bot = TeamsBot()
