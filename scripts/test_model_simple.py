
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer

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

def test_model_loading():
    """Test model loading with cache directory."""
    print_info("Testing model loading with cache directory...")

    cache_dir = Path(__file__).parent.parent / "models" / "cache"
    print_info(f"Cache directory: {cache_dir}")

    try:
        print_info("\nLoading model...")
        model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            cache_folder=str(cache_dir)
        )
        print_success("Model loaded successfully")
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
    test_model_loading()
