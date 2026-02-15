
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

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

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def test_document_processing():
    """Test document processing functionality."""
    print_info("Testing document processing...")

    # Find a sample document to process
    sample_dir = Path(__file__).parent.parent / "data" / "sample_documents"
    pdf_files = list(sample_dir.glob("*.pdf"))

    if not pdf_files:
        print_warning("No PDF files found in sample_documents directory")
        return False

    # Use the first PDF file found
    test_file = pdf_files[1]
    print_info(f"Using test file: {test_file.name}")

    try:
        # Test document processing
        print_info("\n1. Testing document processor...")
        process_result = document_processor.process_document(
            file_path=str(test_file),
            file_type=".pdf",
            metadata={"filename": test_file.name, "intent": "Test Intent"}
        )

        if process_result["success"]:
            print_success("Document processed successfully")
            print_info(f"  Text length: {len(process_result['text'])} characters")
            print_info(f"  Number of chunks: {len(process_result['chunks'])}")
            print_info(f"  Embeddings dimension: {len(process_result['embeddings'][0])}")
        else:
            print_error(f"Failed to process document: {process_result.get('error', 'Unknown error')}")
            return False

        # Test vector store
        print_info("\n2. Testing vector store...")

        # Create a test intent
        db = SessionLocal()
        try:
            intent = db.query(Intent).filter(Intent.name == "Test Intent").first()
            if not intent:
                intent = Intent(
                    name="Test Intent",
                    description="Test intent for document processing",
                    confidence_threshold=0.7
                )
                db.add(intent)
                db.commit()
                db.refresh(intent)
                print_success(f"Created test intent with ID: {intent.id}")
            else:
                print_info(f"Using existing test intent with ID: {intent.id}")

            # Create a test document
            document = Document(
                filename=test_file.name,
                file_path=str(test_file),
                file_type=".pdf",
                content=process_result["text"],
                intent_id=intent.id,
                processed=1
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            print_success(f"Created test document with ID: {document.id}")

            # Add to vector store
            chunks = process_result["chunks"]
            embeddings = process_result["embeddings"]

            chunk_ids = [document.id] * len(chunks)
            chunk_metadata = [
                {
                    "document_id": document.id,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "filename": test_file.name,
                    "intent": "Test Intent"
                }
                for i, chunk in enumerate(chunks)
            ]

            vector_store.add_documents(embeddings, chunk_ids, chunk_metadata)
            vector_store.save_index()
            print_success("Added document chunks to vector store")

            # Clean up
#            db.delete(document)
#            db.commit()
#            print_success("Cleaned up test document")

        finally:
            db.close()

        return True

    except Exception as e:
        print_error(f"Error during document processing test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_document_processing()
