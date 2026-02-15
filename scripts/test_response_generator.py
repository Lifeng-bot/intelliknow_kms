
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.response_generator import ResponseGenerator
from core.document_processor import document_processor
from core.vector_store import vector_store
from app.database import SessionLocal, Document, Intent

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

def test_embedding_model_loading():
    """Test embedding model loading."""
    print_header("Testing Embedding Model Loading")

    # Use mock mode to avoid API calls
    response_generator = ResponseGenerator(mock_mode=True)
    print_info("Using mock mode for response generation")

    if response_generator.embedding_model is not None:
        print_success("Embedding model loaded successfully")
        print_info(f"Model dimension: {response_generator.embedding_model.get_sentence_embedding_dimension()}")
    else:
        print_error("Failed to load embedding model")

def test_generate_query_embedding():
    """Test query embedding generation."""
    print_header("Testing Query Embedding Generation")

    # Use mock mode to avoid API calls
    response_generator = ResponseGenerator(mock_mode=True)

    test_query = "What is the company policy on remote work?"
    print_info(f"Generating embedding for query: '{test_query}'")

    try:
        embedding = response_generator.generate_query_embedding(test_query)
        print_success(f"Embedding generated successfully")
        print_info(f"Embedding dimension: {len(embedding)}")
    except Exception as e:
        print_error(f"Failed to generate embedding: {e}")

def test_get_relevant_documents():
    """Test retrieving relevant documents."""
    print_header("Testing Relevant Document Retrieval")

    # Use mock mode to avoid API calls
    response_generator = ResponseGenerator(mock_mode=True)

    # Generate query embedding
    test_query = "What is the company policy on remote work?"
    query_embedding = response_generator.generate_query_embedding(test_query)

    # Get relevant documents
    print_info(f"Searching for documents related to query: '{test_query}'")

    try:
        relevant_docs = response_generator.get_relevant_documents(query_embedding, limit=5)

        if relevant_docs:
            print_success(f"Found {len(relevant_docs)} relevant documents:")
            for i, doc in enumerate(relevant_docs, 1):
                print_info(f"  [{i}] {doc.get('title')}")
                print_info(f"      Score: {doc.get('score'):.2f}")
                print_info(f"      Content: {doc.get('content')[:100]}...")
        else:
            print_warning("No relevant documents found")
    except Exception as e:
        print_error(f"Failed to retrieve relevant documents: {e}")

def test_generate_response():
    """Test response generation."""
    print_header("Testing Response Generation")

    # Use mock mode to avoid API calls
    response_generator = ResponseGenerator(mock_mode=True)

    # Get some documents to use as context
    db = SessionLocal()
    try:
        documents = db.query(Document).limit(3).all()

        if not documents:
            print_warning("No documents found in database. Please upload some documents first.")
            return

        # Format documents for the response generator
        retrieved_docs = []
        for doc in documents:
            retrieved_docs.append({
                "id": doc.id,
                "title": doc.filename,
                "content": doc.content,
                "score": 0.8
            })

        # Generate response
        test_query = "What is the company policy on remote work?"
        print_info(f"Generating response for query: '{test_query}'")

        try:
            response = response_generator.generate_response(test_query, retrieved_docs, intent="General")

            print_success("Response generated successfully")
            print_info(f"\nResponse: {response.get('response')}")
            print_info(f"\nConfidence: {response.get('confidence'):.2f}")
            print_info(f"\nCitations: {len(response.get('citations', []))}")

            for i, citation in enumerate(response.get('citations', []), 1):
                print_info(f"  [{i}] {citation.get('title')}")
                print_info(f"      {citation.get('snippet')}")

        except Exception as e:
            print_error(f"Failed to generate response: {e}")
            import traceback
            traceback.print_exc()

    finally:
        db.close()

def test_end_to_end_query():
    """Test end-to-end query processing."""
    print_header("Testing End-to-End Query Processing")

    # Use mock mode to avoid API calls
    response_generator = ResponseGenerator(mock_mode=True)

    # Test query
    test_query = "What is the company policy on remote work?"
    print_info(f"Processing query: '{test_query}'")

    try:
        # Generate query embedding
        query_embedding = response_generator.generate_query_embedding(test_query)
        print_success("Query embedding generated")

        # Get relevant documents
        relevant_docs = response_generator.get_relevant_documents(query_embedding, limit=3)

        if not relevant_docs:
            print_warning("No relevant documents found")
            return

        print_success(f"Found {len(relevant_docs)} relevant documents")

        # Generate response
        response = response_generator.generate_response(test_query, relevant_docs, intent="General")

        print_success("Response generated successfully")
        print_info(f"\nResponse: {response.get('response')}")
        print_info(f"\nConfidence: {response.get('confidence'):.2f}")

    except Exception as e:
        print_error(f"Failed to process query: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Initialize database
    from app.database import init_db
    init_db()

    # Run tests
    test_embedding_model_loading()
    test_generate_query_embedding()
    test_get_relevant_documents()
    test_generate_response()
    test_end_to_end_query()

    print_header("All Tests Completed")
