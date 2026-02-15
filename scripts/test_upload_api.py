
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

def test_upload_document():
    """Test uploading a document with detailed error reporting."""
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

            print_info(f"Sending request to {API_BASE_URL}/api/kb/upload")
            response = requests.post(
                f"{API_BASE_URL}/api/kb/upload",
                files=files,
                data=data
            )

        print_info(f"Response status code: {response.status_code}")
        print_info(f"Response headers: {response.headers}")

        if response.status_code == 200:
            print_success("Upload document endpoint is accessible")
            result = response.json()
            print_info(f"Document ID: {result.get('document_id')}")
            print_info(f"Chunks processed: {result.get('chunks_count', 0)}")
            return result
        else:
            print_error(f"Upload document endpoint returned status code {response.status_code}")
            print_error(f"Response content: {response.text}")

            # Try to parse error details
            try:
                error_details = response.json()
                print_error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                pass

            return None
    except Exception as e:
        print_error(f"Failed to upload document: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_upload_document()
