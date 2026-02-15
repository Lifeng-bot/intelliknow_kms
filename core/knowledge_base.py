import os
import shutil
from typing import List, Dict, Optional
from datetime import datetime
from app.config import settings
from app.database import SessionLocal, Document, Intent
from core.document_processor import document_processor
from core.vector_store import vector_store

class KnowledgeBase:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def upload_document(self, file_path: str, filename: str, intent_name: Optional[str] = None) -> Dict:
        """
        Upload and process a document to the knowledge base.

        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            intent_name: Name of the intent space to associate with (optional)

        Returns:
            Dictionary containing upload status and document information
        """
        # Validate file type
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in settings.ALLOWED_FILE_TYPES:
            return {
                "success": False,
                "error": f"Unsupported file type. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            }

        # Get intent ID if provided
        intent_id = None
        if intent_name:
            db = SessionLocal()
            try:
                intent = db.query(Intent).filter(Intent.name == intent_name).first()
                if intent:
                    intent_id = intent.id
            finally:
                db.close()

        # Process document
        process_result = document_processor.process_document(
            file_path=file_path,
            file_type=file_ext,
            metadata={"filename": filename, "intent": intent_name}
        )

        if not process_result["success"]:
            return {
                "success": False,
                "error": process_result.get("error", "Failed to process document")
            }

        # Save file to upload directory
        saved_path = os.path.join(self.upload_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
        shutil.copy(file_path, saved_path)

        # Save document to database
        db = SessionLocal()
        try:
            document = Document(
                filename=filename,
                file_path=saved_path,
                file_type=file_ext,
                content=process_result["text"],
                intent_id=intent_id,
                processed=1
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            # Add to vector store
            chunks = process_result["chunks"]
            embeddings = process_result["embeddings"]

            # Create document IDs for each chunk
            chunk_ids = [document.id] * len(chunks)

            # Create metadata for each chunk
            chunk_metadata = [
                {
                    "document_id": document.id,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "filename": filename,
                    "intent": intent_name
                }
                for i, chunk in enumerate(chunks)
            ]

            # Add to vector store
            vector_store.add_documents(embeddings, chunk_ids, chunk_metadata)
            vector_store.save_index()

            return {
                "success": True,
                "document_id": document.id,
                "filename": filename,
                "chunks_count": len(chunks),
                "intent": intent_name
            }

        except Exception as e:
            db.rollback()
            # Clean up saved file if database operation failed
            if os.path.exists(saved_path):
                os.remove(saved_path)

            return {
                "success": False,
                "error": f"Failed to save document: {str(e)}"
            }

        finally:
            db.close()

    def get_documents(self, intent_name: Optional[str] = None) -> List[Dict]:
        """
        Get all documents in the knowledge base, optionally filtered by intent.

        Args:
            intent_name: Name of the intent space to filter by (optional)

        Returns:
            List of document dictionaries
        """
        db = SessionLocal()
        try:
            query = db.query(Document)

            if intent_name:
                intent = db.query(Intent).filter(Intent.name == intent_name).first()
                if intent:
                    query = query.filter(Document.intent_id == intent.id)

            documents = query.all()

            return [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    "processed": doc.processed == 1,
                    "intent": doc.intent.name if doc.intent else None
                }
                for doc in documents
            ]

        finally:
            db.close()

    def get_document(self, document_id: int) -> Optional[Dict]:
        """
        Get a specific document by ID.

        Args:
            document_id: ID of the document

        Returns:
            Document dictionary or None if not found
        """
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()

            if not doc:
                return None

            return {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "content": doc.content,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "processed": doc.processed == 1,
                "intent": doc.intent.name if doc.intent else None
            }

        finally:
            db.close()

    def delete_document(self, document_id: int) -> Dict:
        """
        Delete a document from the knowledge base.

        Args:
            document_id: ID of the document to delete

        Returns:
            Dictionary containing deletion status
        """
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()

            if not doc:
                return {
                    "success": False,
                    "error": "Document not found"
                }

            # Delete file from filesystem
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)

            # Delete from vector store
            vector_store.delete_document(document_id)
            vector_store.save_index()

            # Delete from database
            db.delete(doc)
            db.commit()

            return {
                "success": True,
                "message": f"Document '{doc.filename}' deleted successfully"
            }

        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": f"Failed to delete document: {str(e)}"
            }

        finally:
            db.close()

    def reprocess_document(self, document_id: int) -> Dict:
        """
        Re-process a document in the knowledge base.

        Args:
            document_id: ID of the document to re-process

        Returns:
            Dictionary containing reprocessing status
        """
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()

            if not doc:
                return {
                    "success": False,
                    "error": "Document not found"
                }

            if not os.path.exists(doc.file_path):
                return {
                    "success": False,
                    "error": "Document file not found"
                }

            # Process document
            process_result = document_processor.process_document(
                file_path=doc.file_path,
                file_type=doc.file_type,
                metadata={"filename": doc.filename, "intent": doc.intent.name if doc.intent else None}
            )

            if not process_result["success"]:
                return {
                    "success": False,
                    "error": process_result.get("error", "Failed to process document")
                }

            # Update document content
            doc.content = process_result["text"]
            doc.processed = 1
            db.commit()

            # Delete old embeddings from vector store
            vector_store.delete_document(document_id)

            # Add new embeddings to vector store
            chunks = process_result["chunks"]
            embeddings = process_result["embeddings"]

            # Create document IDs for each chunk
            chunk_ids = [document_id] * len(chunks)

            # Create metadata for each chunk
            chunk_metadata = [
                {
                    "document_id": document_id,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "filename": doc.filename,
                    "intent": doc.intent.name if doc.intent else None
                }
                for i, chunk in enumerate(chunks)
            ]

            # Add to vector store
            vector_store.add_documents(embeddings, chunk_ids, chunk_metadata)
            vector_store.save_index()

            return {
                "success": True,
                "message": f"Document '{doc.filename}' reprocessed successfully",
                "chunks_count": len(chunks)
            }

        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": f"Failed to reprocess document: {str(e)}"
            }

        finally:
            db.close()

# Global knowledge base instance
knowledge_base = KnowledgeBase()
