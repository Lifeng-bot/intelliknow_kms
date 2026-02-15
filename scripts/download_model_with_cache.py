
import os
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Set the cache directory to our local models directory
cache_dir = Path(__file__).parent.parent / "models" / "cache"
cache_dir.mkdir(parents=True, exist_ok=True)

print(f"Cache directory: {cache_dir}")

# Model to download
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

print(f"Downloading model: {MODEL_NAME}")
print(f"Using cache directory: {cache_dir}")

try:
    # Download and save the model with cache
    model = SentenceTransformer(MODEL_NAME, cache_folder=str(cache_dir))

    # Test the model
    print("\nTesting model...")
    test_text = "This is a test sentence for embedding generation."
    embedding = model.encode([test_text])
    print(f"✓ Model loaded and tested successfully")
    print(f"  Embedding dimension: {len(embedding[0])}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
