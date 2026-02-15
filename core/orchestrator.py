from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from app.config import settings
from app.database import SessionLocal, Intent, Query

class QueryOrchestrator:
    def __init__(self, mock_mode=False):
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
        self.default_confidence_threshold = settings.DEFAULT_CONFIDENCE_THRESHOLD
        self.fallback_intent = settings.FALLBACK_INTENT
        self.mock_mode = mock_mode

    def classify_intent(self, query: str, intents: List[Dict]) -> Tuple[str, float]:
        """
        Classify the intent of a user query using OpenAI's GPT model.

        Args:
            query: The user's query text
            intents: List of available intents with their names and descriptions

        Returns:
            Tuple of (intent_name, confidence_score)
        """
        if not intents:
            return self.fallback_intent, 0.0

        # Mock mode for testing
        if self.mock_mode:
            # Simple keyword-based classification for mock mode
            query_lower = query.lower()

            # Define keywords for each intent
            intent_keywords = {
                "HR": ["hr", "human resources", "leave", "holiday", "employee", "benefit", "salary"],
                "Legal": ["legal", "law", "contract", "compliance", "regulation"],
                "Finance": ["finance", "budget", "expense", "financial", "cost", "accounting"],
                "General": ["general", "information", "help", "support", "policy", "procedure"]
            }

            # Find the best matching intent based on keywords
            best_intent = self.fallback_intent
            best_score = 0.0

            for intent_name, keywords in intent_keywords.items():
                score = sum(1 for keyword in keywords if keyword in query_lower)
                if score > best_score:
                    best_score = score
                    best_intent = intent_name

            # Normalize score to 0-1 range
            confidence = min(best_score / 3.0, 1.0)

            # Validate intent exists
            valid_intents = [intent["name"] for intent in intents]
            if best_intent not in valid_intents:
                best_intent = self.fallback_intent
                confidence = 0.0

            return best_intent, confidence

        # Create prompt for intent classification
        intent_list = "\n".join([f"- {intent['name']}: {intent.get('description', '')}" for intent in intents])

        prompt = f"""
You are an intent classifier for a knowledge management system. Your task is to classify user queries into one of the following intent spaces:

{intent_list}

Analyze the following query and determine which intent space it belongs to. Respond with a JSON object containing:
1. "intent": the name of the most appropriate intent space
2. "confidence": your confidence level in this classification (0.0 to 1.0)

Query: "{query}"

Your response (JSON only):
"""

        try:
            # Log the request details
            print("=" * 80)
            print("DeepSeek Intent Classification API Call:")
            print("=" * 80)
            print(f"Model: {settings.DEEPSEEK_MODEL}")
            print(f"Query: {query}")
            print(f"Temperature: 0.3")
            print(f"Response Format: json_object")
            print("-" * 80)
            print("Available Intents:")
            for intent in intents:
                print(f"  - {intent['name']}: {intent.get('description', '')}")
            print("-" * 80)
            print("Prompt:")
            print(prompt)
            print("=" * 80)

            response = self.client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that classifies user queries into intent spaces."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            # Log the response details
            print("DeepSeek Intent Classification Response:")
            print("=" * 80)
            print(f"Response ID: {response.id}")
            print(f"Model: {response.model}")
            print(f"Usage: {response.usage}")
            print("-" * 80)
            print("Raw Response:")
            print(response.choices[0].message.content)
            print("=" * 80)

            result = response.choices[0].message.content
            import json
            classification = json.loads(result)

            intent_name = classification.get("intent", self.fallback_intent)
            confidence = float(classification.get("confidence", 0.0))

            # Validate intent exists
            valid_intents = [intent["name"] for intent in intents]
            if intent_name not in valid_intents:
                intent_name = self.fallback_intent
                confidence = 0.0

            # Log the final classification result
            print("Final Classification Result:")
            print("=" * 80)
            print(f"Intent: {intent_name}")
            print(f"Confidence: {confidence}")
            print(f"Valid Intent: {intent_name in valid_intents}")
            print("=" * 80)

            return intent_name, confidence

        except Exception as e:
            print("=" * 80)
            print(f"Error classifying intent: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            # Fall back to mock mode if API call fails
            if not self.mock_mode:
                print("Falling back to mock mode for intent classification")
                self.mock_mode = True
                return self.classify_intent(query, intents)
            return self.fallback_intent, 0.0

    def route_query(self, query: str) -> Dict:
        """
        Route a query to the appropriate knowledge base based on intent classification.

        Args:
            query: The user's query text

        Returns:
            Dictionary containing routing information
        """
        db = SessionLocal()
        try:
            # Get all available intents
            intents = db.query(Intent).all()
            intent_list = [{"name": intent.name, "description": intent.description} for intent in intents]

            # Classify intent
            intent_name, confidence = self.classify_intent(query, intent_list)

            # Get intent object
            intent = db.query(Intent).filter(Intent.name == intent_name).first()

            # Check if confidence meets threshold
            threshold = intent.confidence_threshold if intent else self.default_confidence_threshold
            use_intent = confidence >= threshold

            # Log the query
            query_record = Query(
                user_query=query,
                intent_id=intent.id if intent else None,
                confidence=confidence if use_intent else 0.0
            )
            db.add(query_record)
            db.commit()
            db.refresh(query_record)

            return {
                "query_id": query_record.id,
                "intent": intent_name,
                "confidence": confidence,
                "use_intent": use_intent,
                "intent_id": intent.id if intent else None
            }

        finally:
            db.close()

    def get_intent_suggestions(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Get suggestions for improving intent classification accuracy.

        Args:
            query: The user's query text
            limit: Maximum number of suggestions to return

        Returns:
            List of suggested intent mappings
        """
        db = SessionLocal()
        try:
            # Get all available intents
            intents = db.query(Intent).all()
            intent_list = [{"name": intent.name, "description": intent.description} for intent in intents]

            # Classify intent
            intent_name, confidence = self.classify_intent(query, intent_list)

            # If confidence is low, suggest alternative intents
            suggestions = []
            if confidence < self.default_confidence_threshold:
                # Get similar queries from history
                similar_queries = db.query(Query).filter(
                    Query.user_query.contains(query.split()[0])  # Simple similarity check
                ).limit(limit).all()

                for q in similar_queries:
                    if q.intent_id:
                        intent = db.query(Intent).filter(Intent.id == q.intent_id).first()
                        if intent and intent.name != intent_name:
                            suggestions.append({
                                "intent": intent.name,
                                "reason": "Similar historical queries",
                                "confidence": q.confidence
                            })

            return suggestions

        finally:
            db.close()

# Global query orchestrator instance
query_orchestrator = QueryOrchestrator()
