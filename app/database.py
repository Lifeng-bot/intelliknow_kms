from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from app.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database models
class Intent(Base):
    __tablename__ = "intents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    confidence_threshold = Column(Float, default=0.70)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="intent")
    queries = relationship("Query", back_populates="intent")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    intent_id = Column(Integer, ForeignKey("intents.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Integer, default=0)  # 0: not processed, 1: processed

    # Relationships
    intent = relationship("Intent", back_populates="documents")

class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text, nullable=False)
    intent_id = Column(Integer, ForeignKey("intents.id"), nullable=True)
    confidence = Column(Float, nullable=True)
    response = Column(Text, nullable=True)
    citations = Column(Text, nullable=True)  # JSON string of document IDs
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    intent = relationship("Intent", back_populates="queries")

# Initialize database
def init_db():
    Base.metadata.create_all(bind=engine)

    # Create default intents if they don't exist
    db = SessionLocal()
    try:
        default_intents = [
            {"name": "HR", "description": "Human Resources related queries"},
            {"name": "Legal", "description": "Legal department related queries"},
            {"name": "Finance", "description": "Finance department related queries"},
            {"name": "General", "description": "General queries not specific to any department"}
        ]

        for intent_data in default_intents:
            existing = db.query(Intent).filter(Intent.name == intent_data["name"]).first()
            if not existing:
                db_intent = Intent(**intent_data)
                db.add(db_intent)

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
