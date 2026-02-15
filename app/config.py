import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "IntelliKnow KMS"
    VERSION: str = "1.0.0"

    # DeepSeek Configuration
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_TEMPERATURE: float = 0.7
    DEEPSEEK_MAX_TOKENS: int = 500

    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./intelliknow.db")

    # FAISS Configuration
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_MODEL_CACHE_DIR: str = os.getenv("EMBEDDING_MODEL_CACHE_DIR", "./models/cache")
    # Use local model path to avoid connecting to HuggingFace
    LOCAL_EMBEDDING_MODEL_PATH: str = os.getenv("LOCAL_EMBEDDING_MODEL_PATH", "./models/cache/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf")

    # Intent Classification Configuration
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.70
    FALLBACK_INTENT: str = "General"

    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list = [".pdf", ".docx"]
    UPLOAD_DIR: str = "./data/uploads"

    # Analytics Configuration
    ANALYTICS_DIR: str = "./data/analytics"

    class Config:
        case_sensitive = True

settings = Settings()

