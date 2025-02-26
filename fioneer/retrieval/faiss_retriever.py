import faiss
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any
from fioneer.embeddings.vectorizer import EmbeddingGenerator
from pprint import pprint

class FaissRetriever:
    def __init__(self):
        self.index = None
        self.metadata = None
        self.embedding_generator = EmbeddingGenerator()
        
    def load_index(self, index_dir: Path) -> None:
        """Load pre-built FAISS index and metadata"""
        # Load FAISS index
        index_path = index_dir / "earnings.index"
        self.index = faiss.read_index(str(index_path))
        
        # Load metadata
        metadata_path = index_dir / "metadata.json"
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
            
        print(f"Loaded index with {self.index.ntotal} vectors")
        print(f"Loaded {len(self.metadata)} documents")
    
    async def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents given a query"""
        # Generate query embedding
        query_embedding = await self.embedding_generator.generate_embedding(query)
        query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize query vector (since we're using IndexFlatIP)
        faiss.normalize_L2(query_embedding)
        
        # Search in Faiss index
        distances, indices = self.index.search(query_embedding, k)
        
        # Get corresponding metadata
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx != -1:  # FAISS returns -1 for not found
                result = {
                    "metadata": self.metadata[idx],
                    "similarity": float(distance)  # Using dot product similarity as distance
                }
                results.append(result)
            
        return results
    
    def get_document_by_index(self, idx: int) -> Dict[str, Any]:
        """Get document metadata by index"""
        if idx < 0 or idx >= len(self.metadata):
            raise ValueError(f"Index {idx} out of range")
        return self.metadata[idx]

async def create_retriever() -> FaissRetriever:
    """Create and initialize a FaissRetriever instance"""
    retriever = FaissRetriever()
    
    # Load pre-built index
    index_dir = Path("data/index")
    retriever.load_index(index_dir)
    
    return retriever

# Usage example
async def example_usage():
    retriever = await create_retriever()
    
    # Example search
    query = "What were the Q2 revenue expectations for Agilent?"
    results = await retriever.search_similar(query, k=3)
    
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Question: {result['metadata']['question_summary']}")
        print(f"Answer: {result['metadata']['answer_summary']}")
        print(f"Company: {result['metadata']['company']}")
        print(f"Similarity: {result['similarity']:.4f}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage()) 