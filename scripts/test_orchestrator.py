
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import QueryOrchestrator
from app.database import SessionLocal, Intent, Query

# Colors for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def test_classify_intent():
    """Test intent classification functionality."""
    print_header("Testing Intent Classification")

    # Use mock mode to avoid API calls
    orchestrator = QueryOrchestrator(mock_mode=True)
    print_info("Using mock mode for intent classification")

    # Get available intents
    db = SessionLocal()
    try:
        intents = db.query(Intent).all()
        intent_list = [{"name": intent.name, "description": intent.description} for intent in intents]

        print_info(f"Found {len(intents)} intents in database:")
        for intent in intents:
            print_info(f"  - {intent.name}: {intent.description}")

        # Test queries for different intents
        test_queries = [
            "What is the company policy on remote work?",
            "How do I apply for leave?",
            "What are the benefits offered by the company?",
            "Tell me about the financial policies of the company."
        ]

        for query in test_queries:
            print_info(f"\nClassifying query: '{query}'")
            intent_name, confidence = orchestrator.classify_intent(query, intent_list)

            if confidence > 0.7:
                print_success(f"Intent: {intent_name}, Confidence: {confidence:.2f}")
            else:
                print_warning(f"Intent: {intent_name}, Confidence: {confidence:.2f} (Low confidence)")

    finally:
        db.close()

def test_route_query():
    """Test query routing functionality."""
    print_header("Testing Query Routing")

    # Use mock mode to avoid API calls
    orchestrator = QueryOrchestrator(mock_mode=True)
    print_info("Using mock mode for query routing")

    # Test queries
    test_queries = [
        "What is the company policy on remote work?",
        "How do I apply for leave?",
        "What are the benefits offered by the company?"
    ]

    for query in test_queries:
        print_info(f"\nRouting query: '{query}'")
        result = orchestrator.route_query(query)

        print_info(f"Query ID: {result.get('query_id')}")
        print_info(f"Intent: {result.get('intent')}")
        print_info(f"Confidence: {result.get('confidence'):.2f}")
        print_info(f"Use Intent: {result.get('use_intent')}")
        print_info(f"Intent ID: {result.get('intent_id')}")

def test_get_intent_suggestions():
    """Test intent suggestions functionality."""
    print_header("Testing Intent Suggestions")

    # Use mock mode to avoid API calls
    orchestrator = QueryOrchestrator(mock_mode=True)
    print_info("Using mock mode for intent suggestions")

    # Test query
    query = "What is the company policy on remote work?"
    print_info(f"Getting intent suggestions for query: '{query}'")

    suggestions = orchestrator.get_intent_suggestions(query)

    if suggestions:
        print_success(f"Found {len(suggestions)} suggestions:")
        for suggestion in suggestions:
            print_info(f"  - Intent: {suggestion.get('intent')}, Reason: {suggestion.get('reason')}, Confidence: {suggestion.get('confidence'):.2f}")
    else:
        print_warning("No suggestions found")

if __name__ == "__main__":
    # Initialize database
    from app.database import init_db
    init_db()

    # Run tests
    test_classify_intent()
    test_route_query()
    test_get_intent_suggestions()

    print_header("All Tests Completed")
