import os
import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional
import faiss
from app.config import settings

class VectorStore:
    def __init__(self, index_path: Optional[str] = None):
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.index = None
        self.documents = {}  # Store document metadata
        self.dimension = 384  # Default dimension for all-MiniLM-L6-v2

        # Create directory if it doesn't exist
        index_dir = os.path.dirname(self.index_path)
        if index_dir:
            os.makedirs(index_dir, exist_ok=True)

        # Load existing index if available
        self.load_index()

    def create_index(self, dimension: Optional[int] = None):
        """Create a new FAISS index."""
        self.dimension = dimension or self.dimension
        self.index = faiss.IndexFlatL2(self.dimension)

    def add_documents(self, embeddings: List[List[float]], document_ids: List[int], metadata: Optional[List[Dict]] = None):
        """Add documents to the vector store."""
        if self.index is None:
            self.create_index(len(embeddings[0]))

        # Convert embeddings to numpy array
        embeddings_array = np.array(embeddings, dtype='float32')

        # Add to index
        self.index.add(embeddings_array)

        # Store document metadata
        # Use the current index size as the starting key
        start_key = len(self.documents)
        for i, doc_id in enumerate(document_ids):
            self.documents[start_key + i] = {
                "id": doc_id,
                "metadata": metadata[i] if metadata and i < len(metadata) else {}
            }
        
        # Log the added documents
        print("=" * 80)
        print("Add Documents to Vector Store:")
        print("=" * 80)
        print(f"Number of embeddings: {len(embeddings)}")
        print(f"Number of document IDs: {len(document_ids)}")
        print(f"Starting key: {start_key}")
        print(f"Document IDs: {document_ids}")
        for i, (key, doc_id) in enumerate(zip(range(start_key, start_key + len(document_ids)), document_ids), 1):
            print(f"  Chunk {i}:")
            print(f"    Vector Store Key: {key}")
            print(f"    Document ID: {doc_id}")
            if metadata and i-1 < len(metadata):
                print(f"    Metadata: {metadata[i-1]}")
        print("=" * 80)

    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """Search for similar documents."""
        print("=" * 80)
        print("Vector Store Search:")
        print("=" * 80)
        print(f"Number of documents in store: {len(self.documents)}")
        print(f"Search limit (k): {k}")
        
        if self.index is None:
            print("Index is None, returning empty results")
            print("=" * 80)
            return []

        # Convert query to numpy array
        query_array = np.array([query_embedding], dtype='float32')

        # Search
        distances, indices = self.index.search(query_array, k)
        
        print(f"FAISS search returned {len(indices[0])} results")
        print("FAISS indices:", indices[0])
        print("FAISS distances:", distances[0])

        # Return results with metadata
        results = []
        for i, idx in enumerate(indices[0]):
            print(f"\nProcessing result {i+1}:")
            print(f"  FAISS index: {idx}")
            # FAISS returns -1 when there are not enough results
            if idx >= 0 and idx < len(self.documents):
                doc_id = self.documents[idx]["id"]
                distance = float(distances[0][i])
                metadata = self.documents[idx]["metadata"]
                print(f"  Document ID: {doc_id}")
                print(f"  Distance: {distance:.4f}")
                print(f"  Metadata: {metadata}")
                result = {
                    "document_id": doc_id,
                    "distance": distance,
                    "metadata": metadata
                }
                results.append(result)
            else:
                print(f"  Index {idx} is out of range (valid range: 0 to {len(self.documents)-1})")
        
        print(f"\nTotal valid results: {len(results)}")
        print("=" * 80)

        return results

    def save_index(self):
        """Save the FAISS index and document metadata to disk."""
        if self.index is None:
            return

        # Save FAISS index
        faiss.write_index(self.index, f"{self.index_path}.index")

        # Save document metadata
        with open(f"{self.index_path}.metadata", 'wb') as f:
            pickle.dump(self.documents, f)

    def load_index(self):
        """Load the FAISS index and document metadata from disk."""
        index_file = f"{self.index_path}.index"
        metadata_file = f"{self.index_path}.metadata"

        if os.path.exists(index_file) and os.path.exists(metadata_file):
            try:
                # Load FAISS index
                self.index = faiss.read_index(index_file)

                # Load document metadata
                with open(metadata_file, 'rb') as f:
                    self.documents = pickle.load(f)

                return True
            except Exception as e:
                print(f"Error loading index: {e}")
                return False

        return False

    def delete_document(self, document_id: int):
        """Delete a document from the vector store."""
        # Note: FAISS doesn't support direct deletion, so we need to rebuild the index
        # This is a simplified implementation - in production, consider using more advanced approaches
        keys_to_delete = [k for k, v in self.documents.items() if v["id"] == document_id]

        if keys_to_delete:
            for key in keys_to_delete:
                del self.documents[key]

            # Rebuild index (simplified - in production, optimize this)
            self.create_index()
            self.save_index()

# Global vector store instance
vector_store = VectorStore()
