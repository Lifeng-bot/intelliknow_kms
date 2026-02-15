
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer
from app.config import settings

print(f"Model name: {settings.EMBEDDING_MODEL}")
print(f"Cache directory: {settings.EMBEDDING_MODEL_CACHE_DIR}")

# Create cache directory
cache_dir = Path(settings.EMBEDDING_MODEL_CACHE_DIR)
cache_dir.mkdir(parents=True, exist_ok=True)

print("\nLoading model...")
try:
    model = SentenceTransformer(
        settings.EMBEDDING_MODEL,
        cache_folder=str(cache_dir)
    )
    print(f"✓ Model loaded successfully")
    print(f"  Model dimension: {model.get_sentence_embedding_dimension()}")

    # Test embedding generation
    print("\nTesting embedding generation...")
    test_text = "This is a test sentence for embedding generation."
    embedding = model.encode([test_text])
    print(f"✓ Successfully generated embedding for test text")
    print(f"  Embedding dimension: {len(embedding[0])}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
