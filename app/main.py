from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import tempfile
import os

from app.config import settings
from app.database import get_db, SessionLocal, Intent, Query, Document
from core.knowledge_base import knowledge_base
from core.orchestrator import query_orchestrator
from core.response_generator import response_generator

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Gen AI-Powered Knowledge Management System"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class IntentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    confidence_threshold: Optional[float] = None

class IntentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    confidence_threshold: Optional[float] = None

# API Routes

@app.get("/")
def read_root():
    return {
        "message": "Welcome to IntelliKnow KMS API",
        "version": settings.VERSION,
        "docs": "/docs"
    }

@app.post("/api/query")
def process_query(request: QueryRequest):
    """
    Process a user query and return a response with citations.
    """
    try:
        # Route query based on intent
        routing_info = query_orchestrator.route_query(request.query)

        # Generate query embedding
        query_embedding = response_generator.generate_query_embedding(request.query)

        # Get relevant documents
        relevant_docs = response_generator.get_relevant_documents(
            query_embedding=query_embedding,
            intent_id=routing_info["intent_id"] if routing_info["use_intent"] else None
        )

        # Generate response
        response_data = response_generator.generate_response(
            query=request.query,
            retrieved_docs=relevant_docs,
            intent=routing_info["intent"] if routing_info["use_intent"] else None
        )

        # Update query record with response
        db = SessionLocal()
        try:
            query_record = db.query(Query).filter(Query.id == routing_info["query_id"]).first()
            if query_record:
                query_record.response = response_data["response"]
                query_record.citations = str(response_data["citations"])
                db.commit()
        finally:
            db.close()

        return {
            "response": response_data["response"],
            "citations": response_data["citations"],
            "confidence": response_data["confidence"],
            "intent": routing_info["intent"],
            "intent_confidence": routing_info["confidence"]
        }
    except ValueError as e:
        # Handle embedding model errors
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Handle other errors
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/api/query/history")
def get_query_history(limit: int = 100, offset: int = 0):
    """
    Get query history.
    """
    db = SessionLocal()
    try:
        queries = db.query(Query).order_by(Query.timestamp.desc()).offset(offset).limit(limit).all()

        return [
            {
                "id": q.id,
                "query": q.user_query,
                "intent": q.intent.name if q.intent else None,
                "confidence": q.confidence,
                "timestamp": q.timestamp.isoformat() if q.timestamp else None
            }
            for q in queries
        ]
    finally:
        db.close()

@app.post("/api/kb/upload")
def upload_document(
    file: UploadFile = File(...),
    intent: Optional[str] = Form(None)
):
    """
    Upload a document to the knowledge base.
    """
    print(f"Received upload request for file: {file.filename}, intent: {intent}")

    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file.file.read())
        temp_path = temp_file.name
        print(f"Saved uploaded file to temporary location: {temp_path}")

    try:
        # Upload document to knowledge base
        print("Processing document...")
        result = knowledge_base.upload_document(
            file_path=temp_path,
            filename=file.filename,
            intent_name=intent
        )

        if not result["success"]:
            print(f"Document processing failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=400, detail=result["error"])

        print(f"Document processed successfully: {result}")
        return result

    except Exception as e:
        print(f"Error during document upload: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"Cleaned up temporary file: {temp_path}")

@app.get("/api/kb/documents")
def get_documents(intent: Optional[str] = None):
    """
    Get all documents in the knowledge base.
    """
    return knowledge_base.get_documents(intent_name=intent)

@app.get("/api/kb/documents/{document_id}")
def get_document(document_id: int):
    """
    Get a specific document by ID.
    """
    document = knowledge_base.get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document

@app.delete("/api/kb/documents/{document_id}")
def delete_document(document_id: int):
    """
    Delete a document from the knowledge base.
    """
    result = knowledge_base.delete_document(document_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result

@app.post("/api/kb/documents/{document_id}/reprocess")
def reprocess_document(document_id: int):
    """
    Re-process a document in the knowledge base.
    """
    result = knowledge_base.reprocess_document(document_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result

@app.get("/api/intents")
def get_intents():
    """
    Get all intent spaces.
    """
    db = SessionLocal()
    try:
        intents = db.query(Intent).all()

        return [
            {
                "id": intent.id,
                "name": intent.name,
                "description": intent.description,
                "confidence_threshold": intent.confidence_threshold,
                "created_at": intent.created_at.isoformat() if intent.created_at else None,
                "updated_at": intent.updated_at.isoformat() if intent.updated_at else None
            }
            for intent in intents
        ]
    finally:
        db.close()

@app.post("/api/intents")
def create_intent(intent_data: IntentCreate):
    """
    Create a new intent space.
    """
    db = SessionLocal()
    try:
        # Check if intent with same name already exists
        existing = db.query(Intent).filter(Intent.name == intent_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Intent with this name already exists")

        # Create new intent
        new_intent = Intent(
            name=intent_data.name,
            description=intent_data.description,
            confidence_threshold=intent_data.confidence_threshold or settings.DEFAULT_CONFIDENCE_THRESHOLD
        )

        db.add(new_intent)
        db.commit()
        db.refresh(new_intent)

        return {
            "id": new_intent.id,
            "name": new_intent.name,
            "description": new_intent.description,
            "confidence_threshold": new_intent.confidence_threshold,
            "created_at": new_intent.created_at.isoformat() if new_intent.created_at else None,
            "updated_at": new_intent.updated_at.isoformat() if new_intent.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()

@app.put("/api/intents/{intent_id}")
def update_intent(intent_id: int, intent_data: IntentUpdate):
    """
    Update an intent space.
    """
    db = SessionLocal()
    try:
        intent = db.query(Intent).filter(Intent.id == intent_id).first()

        if not intent:
            raise HTTPException(status_code=404, detail="Intent not found")

        # Update intent fields
        if intent_data.name is not None:
            # Check if another intent with the same name exists
            existing = db.query(Intent).filter(
                Intent.name == intent_data.name,
                Intent.id != intent_id
            ).first()

            if existing:
                raise HTTPException(status_code=400, detail="Intent with this name already exists")

            intent.name = intent_data.name

        if intent_data.description is not None:
            intent.description = intent_data.description

        if intent_data.confidence_threshold is not None:
            intent.confidence_threshold = intent_data.confidence_threshold

        db.commit()
        db.refresh(intent)

        return {
            "id": intent.id,
            "name": intent.name,
            "description": intent.description,
            "confidence_threshold": intent.confidence_threshold,
            "created_at": intent.created_at.isoformat() if intent.created_at else None,
            "updated_at": intent.updated_at.isoformat() if intent.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()

@app.delete("/api/intents/{intent_id}")
def delete_intent(intent_id: int):
    """
    Delete an intent space.
    """
    db = SessionLocal()
    try:
        intent = db.query(Intent).filter(Intent.id == intent_id).first()

        if not intent:
            raise HTTPException(status_code=404, detail="Intent not found")

        # Check if intent is used by any documents
        if intent.documents:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete intent that is used by documents. Please reassign or delete those documents first."
            )

        db.delete(intent)
        db.commit()

        return {"message": f"Intent '{intent.name}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()

@app.get("/api/analytics/metrics")
def get_analytics_metrics():
    """
    Get system metrics.
    """
    db = SessionLocal()
    try:
        # Get total counts
        total_documents = db.query(Document).count()
        total_intents = db.query(Intent).count()
        total_queries = db.query(Query).count()

        # Get query counts by intent
        intent_query_counts = {}
        for intent in db.query(Intent).all():
            intent_query_counts[intent.name] = db.query(Query).filter(Query.intent_id == intent.id).count()

        # Get recent queries
        recent_queries = db.query(Query).order_by(Query.timestamp.desc()).limit(10).all()

        return {
            "total_documents": total_documents,
            "total_intents": total_intents,
            "total_queries": total_queries,
            "intent_query_counts": intent_query_counts,
            "recent_queries": [
                {
                    "id": q.id,
                    "query": q.user_query,
                    "intent": q.intent.name if q.intent else None,
                    "confidence": q.confidence,
                    "timestamp": q.timestamp.isoformat() if q.timestamp else None
                }
                for q in recent_queries
            ]
        }

    finally:
        db.close()

@app.get("/api/analytics/history")
def get_analytics_history(limit: int = 100, offset: int = 0):
    """
    Get query history for analytics.
    """
    db = SessionLocal()
    try:
        queries = db.query(Query).order_by(Query.timestamp.desc()).offset(offset).limit(limit).all()

        return [
            {
                "id": q.id,
                "query": q.user_query,
                "intent": q.intent.name if q.intent else None,
                "confidence": q.confidence,
                "response": q.response,
                "citations": q.citations,
                "timestamp": q.timestamp.isoformat() if q.timestamp else None
            }
            for q in queries
        ]

    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
