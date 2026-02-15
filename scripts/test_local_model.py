
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Test loading the model from the local path
model_path = "models/embedding_models/sentence-transformers_all-MiniLM-L6-v2"

print(f"Testing model loading from: {model_path}")
print(f"Path exists: {Path(model_path).exists()}")

try:
    print("\nLoading model...")
    model = SentenceTransformer(model_path)
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
