from typing import List, Dict, Optional
from pathlib import Path
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.database import SessionLocal, Document

class ResponseGenerator:
    def __init__(self, mock_mode=False):
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
        self._embedding_model = None
        self.mock_mode = mock_mode
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
            print("The system will start but embedding-based features may not work properly.")
            print("Please check your internet connection or configure a proxy to access HuggingFace.")
            self._embedding_model = None

    @property
    def embedding_model(self):
        """Get the embedding model."""
        return self._embedding_model

    def generate_response(self, query: str, retrieved_docs: List[Dict], intent: Optional[str] = None) -> Dict:
        """
        Generate a response to a user query based on retrieved documents.

        Args:
            query: The user's query text
            retrieved_docs: List of retrieved documents with their content and metadata
            intent: The classified intent of the query (optional)

        Returns:
            Dictionary containing the generated response and citations
        """
        if not retrieved_docs:
            return {
                "response": "I couldn't find any relevant information in the knowledge base to answer your question. Please try rephrasing your question or contact support for assistance.",
                "citations": [],
                "confidence": 0.0
            }

        # Prepare context from retrieved documents
        context = self._prepare_context(retrieved_docs)

        # Generate response using DeepSeek
        response_text = self._generate_with_deepseek(query, context, intent)

        # Extract citations
        citations = self._extract_citations(retrieved_docs)

        # Calculate confidence based on document relevance
        confidence = self._calculate_confidence(retrieved_docs)

        return {
            "response": response_text,
            "citations": citations,
            "confidence": confidence
        }

    def _prepare_context(self, retrieved_docs: List[Dict]) -> str:
        """Prepare context from retrieved documents.
        
        This method intelligently selects content from retrieved documents to provide
        the most relevant information to the model. It considers:
        1. Document similarity score (higher score = more relevant)
        2. Content length (balance between detail and token usage)
        3. Multiple relevant segments from the same document
        """
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            doc_content = doc.get("content", "")
            doc_title = doc.get("title", f"Document {i}")
            score = doc.get("score", 0.0)
            
            # Log document processing
            print("=" * 80)
            print(f"Preparing Context - Document {i}:")
            print("=" * 80)
            print(f"Title: {doc_title}")
            print(f"Score: {score:.4f}")
            print(f"Content Length: {len(doc_content)} characters")
            
            # Determine how much content to include based on relevance score
            # Similarity score is calculated as 1.0 - distance, range is negative to 1
            # Most scores are negative, with occasional positive scores (e.g., 0.12)
            # Higher score = more relevant = more content
            # Expanded intervals to better handle the actual score distribution
            if score >= 0.0:
                max_chars = 2500  # Positive score, very highly relevant, include most content
            elif score >= -0.2:
                max_chars = 2000  # Close to zero, highly relevant, include more content
            elif score >= -0.5:
                max_chars = 1500  # Moderately relevant
            elif score >= -1.0:
                max_chars = 1000  # Somewhat relevant
            elif score >= -2.0:
                max_chars = 600   # Less relevant
            else:
                max_chars = 300   # Low relevance, minimal content
            
            print(f"Max Characters to Include: {max_chars}")
            
            # If content is shorter than max_chars, include all of it
            if len(doc_content) <= max_chars:
                selected_content = doc_content
                print("Content is shorter than max_chars, including all content")
            else:
                # For longer documents, include the beginning and end
                # This captures both introduction and conclusion
                first_part = doc_content[:max_chars // 2]
                last_part = doc_content[-(max_chars // 2):]
                selected_content = f"{first_part}\n\n... [content omitted] ...\n\n{last_part}"
                print(f"Content is longer than max_chars, including first and last parts")
            
            # Add to context
            context_parts.append(f"[{i}] {doc_title}:\n{selected_content}")
            print("=" * 80)

        return "\n\n".join(context_parts)

    def _generate_with_deepseek(self, query: str, context: str, intent: Optional[str] = None) -> str:
        """Generate response using DeepSeek model."""
        system_prompt = """
You are a helpful assistant for a knowledge management system. Your task is to answer user questions based on the provided context from the knowledge base.

Guidelines:
1. Provide concise, accurate answers based on the context
2. Cite the sources using [1], [2], etc. notation
3. If the context doesn't contain enough information, acknowledge this limitation
4. Be professional and helpful in your responses
"""

        user_prompt = f"""
Context from the knowledge base:
{context}

User Query: {query}
"""

        if intent:
            user_prompt += f"\n\nIntent: {intent}"

        # Mock mode for testing
        if self.mock_mode:
            print("=" * 80)
            print("DeepSeek API Call (Mock Mode):")
            print("=" * 80)
            print(f"Query: {query}")
            print(f"Intent: {intent}")
            print(f"Context Length: {len(context)} characters")
            print("=" * 80)
            # Simple mock response based on context
            if context:
                response_text = f"Based on the provided documents, here's what I found regarding your query about '{query}':\n\nThe documents contain relevant information that addresses your question. Please refer to the cited sources for more details."
            else:
                response_text = "I couldn't find any relevant information in the knowledge base to answer your question. Please try rephrasing your question or contact support for assistance."
            print(f"Response: {response_text}")
            print("=" * 80)
            return response_text

        try:
            # Log the request details
            print("=" * 80)
            print("DeepSeek API Call:")
            print("=" * 80)
            print(f"Model: {settings.DEEPSEEK_MODEL}")
            print(f"Temperature: {settings.DEEPSEEK_TEMPERATURE}")
            print(f"Max Tokens: {settings.DEEPSEEK_MAX_TOKENS}")
            print("-" * 80)
            print("System Prompt:")
            print(system_prompt)
            print("-" * 80)
            print("User Prompt:")
            print(user_prompt)
            print("=" * 80)

            response = self.client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.DEEPSEEK_TEMPERATURE,
                max_tokens=settings.DEEPSEEK_MAX_TOKENS
            )

            # Log the response details
            print("DeepSeek API Response:")
            print("=" * 80)
            print(f"Response ID: {response.id}")
            print(f"Model: {response.model}")
            print(f"Usage: {response.usage}")
            print("-" * 80)
            print("Response Content:")
            print(response.choices[0].message.content)
            print("=" * 80)

            return response.choices[0].message.content

        except Exception as e:
            print("=" * 80)
            print(f"Error generating response: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            # Fall back to mock mode if API call fails
            if not self.mock_mode:
                print("Falling back to mock mode for response generation")
                self.mock_mode = True
                return self._generate_with_deepseek(query, context, intent)
            return "I apologize, but I encountered an error while generating a response. Please try again later."

    def _extract_citations(self, retrieved_docs: List[Dict]) -> List[Dict]:
        """Extract citation information from retrieved documents."""
        citations = []
        for i, doc in enumerate(retrieved_docs, 1):
            citation = {
                "id": doc.get("id", i),
                "title": doc.get("title", f"Document {i}"),
                "snippet": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", "")
            }
            citations.append(citation)

        return citations

    def _calculate_confidence(self, retrieved_docs: List[Dict]) -> float:
        """Calculate confidence score based on document relevance."""
        print("=" * 80)
        print("Calculate Confidence:")
        print("=" * 80)
        
        if not retrieved_docs:
            print("No retrieved documents, returning confidence: 0.0")
            print("=" * 80)
            return 0.0

        # Simple confidence calculation based on document scores
        scores = [doc.get("score", 0.0) for doc in retrieved_docs]
        print(f"Number of documents: {len(retrieved_docs)}")
        print("Individual scores:")
        for i, (doc, score) in enumerate(zip(retrieved_docs, scores), 1):
            print(f"  Document {i} ({doc.get('title', 'Unknown')}): {score:.4f}")
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        print(f"Average score: {avg_score:.4f}")

        # Normalize to 0-1 range based on actual score distribution
        # Similarity score range is typically from -2.0 to 1.0
        # Map -2.0 to 0.0, and 1.0 to 1.0
        min_score = -2.0
        max_score = 1.0
        
        if avg_score >= max_score:
            normalized_score = 1.0
        elif avg_score <= min_score:
            normalized_score = 0.0
        else:
            # Linear normalization: (avg_score - min_score) / (max_score - min_score)
            normalized_score = (avg_score - min_score) / (max_score - min_score)
        
        # Ensure the result is within 0-1 range
        normalized_score = max(0.0, min(normalized_score, 1.0))
        
        print(f"Normalized confidence: {normalized_score:.4f}")
        print("=" * 80)
        
        return normalized_score

    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a query."""
        if self.embedding_model is None:
            raise ValueError("Embedding model is not loaded. Please check the model configuration and try again.")
        
        # Log the input query
        print("=" * 80)
        print("Local Embedding Model - Generate Query Embedding:")
        print("=" * 80)
        print(f"Input Query: {query}")
        print(f"Query Length: {len(query)} characters")
        print(f"Model: {type(self.embedding_model).__name__}")
        
        # Generate embedding
        embedding = self.embedding_model.encode(query, convert_to_numpy=True)
        
        # Log the result
        print(f"Embedding Dimension: {len(embedding)}")
        print(f"Embedding Type: {type(embedding).__name__}")
        print(f"First 5 Values: {embedding[:5]}")
        print(f"Last 5 Values: {embedding[-5:]}")
        print("=" * 80)
        
        return embedding.tolist()

    def get_relevant_documents(self, query_embedding: List[float], intent_id: Optional[int] = None, limit: int = 5) -> List[Dict]:
        """Get relevant documents based on query embedding and optional intent filter."""
        from core.vector_store import vector_store

        # Log input parameters
        print("=" * 80)
        print("Get Relevant Documents:")
        print("=" * 80)
        print(f"Intent ID: {intent_id}")
        print(f"Limit: {limit}")
        print(f"Query Embedding Dimension: {len(query_embedding)}")
        
        # Search vector store
        results = vector_store.search(query_embedding, k=limit)
        
        # Log search results
        print(f"Vector Store Results: {len(results)} documents found")
        for i, result in enumerate(results, 1):
            print(f"  Result {i}:")
            print(f"    Document ID: {result['document_id']}")
            print(f"    Distance: {result['distance']:.4f}")
            print(f"    Similarity Score: {1.0 - result['distance']:.4f}")
        print("=" * 80)

        # Filter by intent if specified
        if intent_id is not None:
            print(f"\nFiltering by Intent ID: {intent_id}")
            db = SessionLocal()
            try:
                filtered_results = []
                for i, result in enumerate(results, 1):
                    print(f"\nProcessing result {i}:")
                    print(f"  Vector Store Document ID: {result['document_id']}")
                    print(f"  Distance: {result['distance']:.4f}")
                    print(f"  Similarity Score: {1.0 - result['distance']:.4f}")
                    
                    doc = db.query(Document).filter(Document.id == result["document_id"]).first()
                    if doc:
                        print(f"  Found document in database:")
                        print(f"    ID: {doc.id}")
                        print(f"    Title: {doc.filename}")
                        print(f"    Intent ID: {doc.intent_id}")
                        
                        if doc.intent_id == intent_id or doc.intent_id is None:
                            print(f"  [OK] Document matches intent filter (Intent ID: {intent_id})")
                            filtered_results.append({
                                "id": doc.id,
                                "title": doc.filename,
                                "content": doc.content,
                                "score": 1.0 - result["distance"],  # Convert distance to similarity score
                                "metadata": result["metadata"]
                            })
                        else:
                            print(f"  [X] Document does not match intent filter (Expected: {intent_id}, Got: {doc.intent_id})")
                    else:
                        print(f"  [X] Document not found in database")
                
                print(f"\nFiltered Results (Intent ID={intent_id}): {len(filtered_results)} documents")
                for i, doc in enumerate(filtered_results, 1):
                    print(f"  Document {i}:")
                    print(f"    ID: {doc['id']}")
                    print(f"    Title: {doc['title']}")
                    print(f"    Score: {doc['score']:.4f}")
                print("=" * 80)
                return filtered_results
            finally:
                db.close()

        # Return all results without intent filter
        db = SessionLocal()
        try:
            formatted_results = []
            for result in results:
                doc = db.query(Document).filter(Document.id == result["document_id"]).first()
                if doc:
                    formatted_results.append({
                        "id": doc.id,
                        "title": doc.filename,
                        "content": doc.content,
                        "score": 1.0 - result["distance"],  # Convert distance to similarity score
                        "metadata": result["metadata"]
                    })
            print(f"Formatted Results: {len(formatted_results)} documents")
            for i, doc in enumerate(formatted_results, 1):
                print(f"  Document {i}:")
                print(f"    ID: {doc['id']}")
                print(f"    Title: {doc['title']}")
                print(f"    Score: {doc['score']:.4f}")
            print("=" * 80)
            return formatted_results
        finally:
            db.close()

# Global response generator instance
response_generator = ResponseGenerator()
