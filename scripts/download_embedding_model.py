
import os
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Model to download
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Local directory to save the model
LOCAL_MODEL_DIR = Path(__file__).parent.parent / "models" / "embedding_models"
LOCAL_MODEL_DIR.mkdir(parents=True, exist_ok=True)

print(f"Downloading model: {MODEL_NAME}")
print(f"Saving to: {LOCAL_MODEL_DIR}")

try:
    # Download and save the model
    model = SentenceTransformer(MODEL_NAME)
    model.save(str(LOCAL_MODEL_DIR / MODEL_NAME.replace("/", "_")))

    print(f"Model successfully downloaded and saved to: {LOCAL_MODEL_DIR / MODEL_NAME.replace('/', '_')}")
except Exception as e:
    print(f"Error downloading model: {str(e)}")
