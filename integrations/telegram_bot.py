
import asyncio
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from app.config import settings
from core.orchestrator import query_orchestrator
from core.response_generator import response_generator

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram Bot for IntelliKnow KMS"""

    def __init__(self):
        self.application = None
        self._initialize_bot()

    def _initialize_bot(self):
        """Initialize the Telegram bot application."""
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not configured. Telegram bot will not be available.")
            return

        try:
            # Create application
            self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

            # Register handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("history", self.history_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))

            logger.info("Telegram bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            self.application = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        welcome_message = """
🤖 Welcome to IntelliKnow KMS Bot!

I can help you find information from our knowledge base. Just ask me a question!

Commands:
/start - Start the bot
/help - Show help message
/history - Show your query history

Simply type your question and I'll search the knowledge base for relevant information.
        """
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        help_message = """
📚 IntelliKnow KMS Bot Help

How to use:
1. Simply type your question in natural language
2. I'll search the knowledge base and provide relevant information
3. You can ask follow-up questions for clarification

Available Commands:
/start - Start the bot
/help - Show this help message
/history - Show your recent query history

Example questions:
- What is the company's leave policy?
- How do I submit an expense report?
- What are the working hours?

Tips:
- Be specific in your questions
- Use relevant keywords
- Ask one question at a time
        """
        await update.message.reply_text(help_message)

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /history command."""
        user_id = update.effective_user.id

        try:
            # Get query history from orchestrator
            # Note: This would need to be implemented in the orchestrator
            # For now, we'll return a placeholder message
            history_message = f"""
📋 Your Query History

User ID: {user_id}

Recent queries will be displayed here.
            """
            await update.message.reply_text(history_message)
        except Exception as e:
            logger.error(f"Error fetching history for user {user_id}: {e}")
            await update.message.reply_text("Sorry, I couldn't fetch your query history. Please try again later.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages from users."""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        query_text = update.message.text

        logger.info(f"Received query from user {user_id} ({user_name}): {query_text}")

        # Send typing indicator
        await update.message.chat.send_action("typing")

        try:
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

            # Format the response for Telegram
            response_text = self._format_response(
                response=response_data["response"],
                citations=response_data["citations"],
                confidence=response_data["confidence"],
                intent=routing_info["intent"]
            )

            # Send the response
            await update.message.reply_text(response_text, parse_mode="Markdown")

            logger.info(f"Response sent to user {user_id} successfully")

        except Exception as e:
            logger.error(f"Error processing query from user {user_id}: {e}")
            await update.message.reply_text(
                "Sorry, I encountered an error while processing your query. Please try again later."
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()

        # Handle different callback actions
        # This can be expanded to support more interactive features
        if query.data == "show_more":
            await query.edit_message_text("More information will be displayed here.")

    def _format_response(self, response: str, citations: list, confidence: float, intent: str) -> str:
        """Format the response for Telegram."""
        formatted_response = f"📌 **Answer:**\n\n{response}\n\n"

        # Add confidence level
        confidence_emoji = "🔴" if confidence < 0.3 else "🟡" if confidence < 0.7 else "🟢"
        formatted_response += f"{confidence_emoji} **Confidence:** {confidence:.2%}\n"

        # Add intent
        if intent:
            formatted_response += f"📂 **Intent:** {intent}\n"

        # Add citations if available
        if citations:
            formatted_response += "\n📚 **Sources:**\n"
            for i, citation in enumerate(citations, 1):
                title = citation.get("title", f"Document {i}")
                formatted_response += f"{i}. {title}\n"

        return formatted_response

    def run(self):
        """Run the Telegram bot."""
        if not self.application:
            logger.error("Cannot run bot: Application not initialized")
            return

        try:
            # Start the bot
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"Error running Telegram bot: {e}")

    def run_webhook(self):
        """Run the Telegram bot with webhook."""
        if not self.application:
            logger.error("Cannot run bot with webhook: Application not initialized")
            return

        try:
            # Set webhook
            self.application.run_webhook(
                listen="0.0.0.0",
                port=settings.TELEGRAM_WEBHOOK_PORT,
                url_path=settings.TELEGRAM_WEBHOOK_PATH,
                webhook_url=f"{settings.TELEGRAM_WEBHOOK_URL}{settings.TELEGRAM_WEBHOOK_PATH}"
            )
        except Exception as e:
            logger.error(f"Error running Telegram bot with webhook: {e}")


# Global Telegram bot instance
telegram_bot = TelegramBot()
