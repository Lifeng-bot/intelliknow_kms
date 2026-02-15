
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document_processor import document_processor
from core.response_generator import response_generator

print("Testing embedding model loading...")

# Test document processor embedding model
print("\n1. Testing document_processor.embedding_model...")
try:
    model = document_processor.embedding_model
    if model:
        print(f"✓ Document processor embedding model loaded successfully")
        print(f"  Model dimension: {model.get_sentence_embedding_dimension()}")
    else:
        print("✗ Failed to load document processor embedding model")
except Exception as e:
    print(f"✗ Error loading document processor embedding model: {e}")

# Test response generator embedding model
print("\n2. Testing response_generator.embedding_model...")
try:
    model = response_generator.embedding_model
    if model:
        print(f"✓ Response generator embedding model loaded successfully")
        print(f"  Model dimension: {model.get_sentence_embedding_dimension()}")
    else:
        print("✗ Failed to load response generator embedding model")
except Exception as e:
    print(f"✗ Error loading response generator embedding model: {e}")

# Test embedding generation
print("\n3. Testing embedding generation...")
try:
    test_text = "This is a test sentence for embedding generation."
    embedding = document_processor.embedding_model.encode([test_text])
    print(f"✓ Successfully generated embedding for test text")
    print(f"  Embedding dimension: {len(embedding[0])}")
except Exception as e:
    print(f"✗ Error generating embedding: {e}")

print("\nAll tests completed!")
