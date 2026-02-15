import os
import json
from typing import List, Dict, Optional
from pathlib import Path
import PyPDF2
from docx import Document
from sentence_transformers import SentenceTransformer
import numpy as np
from app.config import settings

class DocumentProcessor:
    def __init__(self):
        self._embedding_model = None
        self.chunk_size = 500
        self.chunk_overlap = 50
        # Load the model during initialization
        self._load_embedding_model()

    def _load_embedding_model(self):
        """Load the embedding model."""
        try:
            # Try to load from local path first
            local_model_path = Path(settings.LOCAL_EMBEDDING_MODEL_PATH)

            if local_model_path.exists() and local_model_path.is_dir():
                print(f"Loading embedding model from local path: {settings.LOCAL_EMBEDDING_MODEL_PATH}")
                self._embedding_model = SentenceTransformer(str(local_model_path))
                print("Embedding model loaded successfully from local path")
            else:
                # Fall back to cache directory
                cache_dir = Path(settings.EMBEDDING_MODEL_CACHE_DIR)
                cache_dir.mkdir(parents=True, exist_ok=True)

                print(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
                print(f"Using cache directory: {cache_dir}")

                self._embedding_model = SentenceTransformer(
                    settings.EMBEDDING_MODEL,
                    cache_folder=str(cache_dir)
                )
                print("Embedding model loaded successfully")
        except Exception as e:
            import traceback
            print(f"Warning: Failed to load embedding model: {e}")
            traceback.print_exc()
            print("Document processing features may not work properly.")
            print("Please check your internet connection or configure a proxy to access HuggingFace.")
            self._embedding_model = None

    @property
    def embedding_model(self):
        """Get the embedding model."""
        return self._embedding_model

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
        return text

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return ""
        return text

    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text from document based on file type."""
        if file_type.lower() == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_type.lower() == ".docx":
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for embedding."""
        chunks = []
        words = text.split()

        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = " ".join(words[i:i + self.chunk_size])
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)

        return chunks

    def create_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """Create embeddings for text chunks."""
        if self.embedding_model is None:
            raise ValueError("Embedding model is not loaded. Please check the model configuration and try again.")
        
        # Log the input chunks
        print("=" * 80)
        print("Local Embedding Model - Create Document Chunks Embeddings:")
        print("=" * 80)
        print(f"Number of Chunks: {len(chunks)}")
        print(f"Model: {type(self.embedding_model).__name__}")
        print("-" * 80)
        for i, chunk in enumerate(chunks, 1):
            preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
            print(f"Chunk {i}: {preview}")
        print("=" * 80)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks, convert_to_numpy=True)
        
        # Log the results
        print("Embedding Generation Results:")
        print("=" * 80)
        print(f"Total Embeddings: {len(embeddings)}")
        print(f"Embedding Dimension: {len(embeddings[0]) if len(embeddings) > 0 else 0}")
        print(f"Embeddings Type: {type(embeddings).__name__}")
        print("-" * 80)
        for i, embedding in enumerate(embeddings, 1):
            print(f"Embedding {i}:")
            print(f"  Dimension: {len(embedding)}")
            print(f"  First 5 Values: {embedding[:5]}")
            print(f"  Last 5 Values: {embedding[-5:]}")
        print("=" * 80)
        
        return embeddings.tolist()

    def process_document(self, file_path: str, file_type: str, metadata: Optional[Dict] = None) -> Dict:
        """Process a document and return its chunks and embeddings."""
        # Extract text from document
        text = self.extract_text(file_path, file_type)
        if not text:
            return {"success": False, "error": "Failed to extract text from document"}

        # Chunk the text
        chunks = self.chunk_text(text)
        if not chunks:
            return {"success": False, "error": "Failed to create text chunks"}

        # Create embeddings
        embeddings = self.create_embeddings(chunks)

        return {
            "success": True,
            "text": text,
            "chunks": chunks,
            "embeddings": embeddings,
            "metadata": metadata or {}
        }

# Global document processor instance
document_processor = DocumentProcessor()
