
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer
from app.config import settings

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

def test_local_model_loading():
    """Test local model loading."""
    print_info("Testing local model loading...")

    local_model_path = Path(settings.LOCAL_EMBEDDING_MODEL_PATH)
    print_info(f"Local model path: {settings.LOCAL_EMBEDDING_MODEL_PATH}")
    print_info(f"Path exists: {local_model_path.exists()}")

    try:
        print_info("\nLoading model from local path...")
        model = SentenceTransformer(str(local_model_path))
        print_success("Model loaded successfully from local path")
        print_info(f"  Model dimension: {model.get_sentence_embedding_dimension()}")

        # Test embedding generation
        print_info("\nTesting embedding generation...")
        test_text = "This is a test sentence for embedding generation."
        embedding = model.encode([test_text])
        print_success("Embedding generated successfully")
        print_info(f"  Embedding dimension: {len(embedding[0])}")

        return True

    except Exception as e:
        print_error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_local_model_loading()
