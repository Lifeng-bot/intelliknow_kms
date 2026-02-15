
import requests
import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# API base URL
API_BASE_URL = "http://localhost:8000"

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

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def test_root_endpoint():
    """Test the root endpoint."""
    print_info("Testing root endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            print_success("Root endpoint is accessible")
            data = response.json()
            print_info(f"API Version: {data.get('version', 'Unknown')}")
            print_info(f"Documentation URL: {data.get('docs', 'Unknown')}")
            return True
        else:
            print_error(f"Root endpoint returned status code {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to connect to root endpoint: {str(e)}")
        return False

def test_get_analytics_metrics():
    """Test getting analytics metrics."""
    print_info("Testing analytics metrics endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/analytics/metrics")
        if response.status_code == 200:
            print_success("Analytics metrics endpoint is accessible")
            data = response.json()
            print_info(f"Total Documents: {data.get('total_documents', 0)}")
            print_info(f"Total Intents: {data.get('total_intents', 0)}")
            print_info(f"Total Queries: {data.get('total_queries', 0)}")
            return True
        else:
            print_error(f"Analytics metrics endpoint returned status code {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to get analytics metrics: {str(e)}")
        return False

def test_get_intents():
    """Test getting all intents."""
    print_info("Testing get intents endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/intents")
        if response.status_code == 200:
            print_success("Get intents endpoint is accessible")
            intents = response.json()
            print_info(f"Number of intents: {len(intents)}")
            return intents
        else:
            print_error(f"Get intents endpoint returned status code {response.status_code}")
            return []
    except Exception as e:
        print_error(f"Failed to get intents: {str(e)}")
        return []

def test_create_intent():
    """Test creating a new intent."""
    print_info("Testing create intent endpoint...")
    try:
        intent_data = {
            "name": "Test Intent",
            "description": "This is a test intent created by the test script",
            "confidence_threshold": 0.7
        }
        response = requests.post(
            f"{API_BASE_URL}/api/intents",
            json=intent_data
        )
        if response.status_code == 200:
            print_success("Create intent endpoint is accessible")
            intent = response.json()
            print_info(f"Created intent with ID: {intent.get('id')}")
            return intent
        else:
            print_error(f"Create intent endpoint returned status code {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Failed to create intent: {str(e)}")
        return None

def test_get_documents():
    """Test getting all documents."""
    print_info("Testing get documents endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/kb/documents")
        if response.status_code == 200:
            print_success("Get documents endpoint is accessible")
            documents = response.json()
            print_info(f"Number of documents: {len(documents)}")
            return documents
        else:
            print_error(f"Get documents endpoint returned status code {response.status_code}")
            return []
    except Exception as e:
        print_error(f"Failed to get documents: {str(e)}")
        return []

def test_upload_document():
    """Test uploading a document."""
    print_info("Testing upload document endpoint...")

    # Find a sample document to upload
    sample_dir = Path(__file__).parent.parent / "data" / "sample_documents"
    pdf_files = list(sample_dir.glob("*.pdf"))

    if not pdf_files:
        print_warning("No PDF files found in sample_documents directory")
        return None

    # Use the first PDF file found
    test_file = pdf_files[0]
    print_info(f"Using test file: {test_file.name}")

    try:
        with open(test_file, "rb") as f:
            files = {"file": (test_file.name, f, "application/pdf")}
            data = {"intent": "Test Intent"}
            response = requests.post(
                f"{API_BASE_URL}/api/kb/upload",
                files=files,
                data=data
            )

        if response.status_code == 200:
            print_success("Upload document endpoint is accessible")
            result = response.json()
            print_info(f"Document ID: {result.get('document_id')}")
            print_info(f"Chunks processed: {result.get('chunks_processed', 0)}")
            return result
        else:
            print_error(f"Upload document endpoint returned status code {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Failed to upload document: {str(e)}")
        return None

def test_query():
    """Test the query endpoint."""
    print_info("Testing query endpoint...")
    try:
        query_data = {
            "query": "What is the expense reimbursement policy?"
        }
        response = requests.post(
            f"{API_BASE_URL}/api/query",
            json=query_data
        )
        if response.status_code == 200:
            print_success("Query endpoint is accessible")
            result = response.json()
            print_info(f"Response: {result.get('response', 'No response')[:100]}...")
            print_info(f"Confidence: {result.get('confidence', 0.0)}")
            print_info(f"Intent: {result.get('intent', 'Unknown')}")
            return result
        else:
            print_error(f"Query endpoint returned status code {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Failed to query: {str(e)}")
        return None

def test_get_query_history():
    """Test getting query history."""
    print_info("Testing get query history endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/query/history?limit=5")
        if response.status_code == 200:
            print_success("Get query history endpoint is accessible")
            queries = response.json()
            print_info(f"Number of queries: {len(queries)}")
            return queries
        else:
            print_error(f"Get query history endpoint returned status code {response.status_code}")
            return []
    except Exception as e:
        print_error(f"Failed to get query history: {str(e)}")
        return []

def test_delete_document(document_id):
    """Test deleting a document."""
    print_info(f"Testing delete document endpoint for document ID {document_id}...")
    try:
        response = requests.delete(f"{API_BASE_URL}/api/kb/documents/{document_id}")
        if response.status_code == 200:
            print_success("Delete document endpoint is accessible")
            result = response.json()
            print_info(f"Result: {result.get('message', 'No message')}")
            return True
        else:
            print_error(f"Delete document endpoint returned status code {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Failed to delete document: {str(e)}")
        return False

def test_delete_intent(intent_id):
    """Test deleting an intent."""
    print_info(f"Testing delete intent endpoint for intent ID {intent_id}...")
    try:
        response = requests.delete(f"{API_BASE_URL}/api/intents/{intent_id}")
        if response.status_code == 200:
            print_success("Delete intent endpoint is accessible")
            result = response.json()
            print_info(f"Result: {result.get('message', 'No message')}")
            return True
        else:
            print_error(f"Delete intent endpoint returned status code {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Failed to delete intent: {str(e)}")
        return False

def run_all_tests():
    """Run all tests."""
    print_header("IntelliKnow KMS Backend API Tests")

    # Test root endpoint
    if not test_root_endpoint():
        print_error("Cannot connect to API server. Please make sure the server is running.")
        return False

    # Test analytics metrics
    test_get_analytics_metrics()

    # Test intents
    print_header("Testing Intent Endpoints")
    intents = test_get_intents()
    test_intent = test_create_intent()

    # Test documents
    print_header("Testing Document Endpoints")
    documents = test_get_documents()
    upload_result = test_upload_document()

    # Test queries
    print_header("Testing Query Endpoints")
    query_result = test_query()
    query_history = test_get_query_history()

    # Cleanup
    print_header("Cleanup")
    if upload_result and "document_id" in upload_result:
        test_delete_document(upload_result["document_id"])

    if test_intent and "id" in test_intent:
        test_delete_intent(test_intent["id"])

    print_header("Test Summary")
    print_success("All tests completed!")
    return True

if __name__ == "__main__":
    run_all_tests()
