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
        
    def load_data(self, embeddings_path: str, metadata_path: str) -> None:
        """Load embeddings and metadata"""
        # Load embeddings
        embeddings = np.load(embeddings_path)
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
            
        # Initialize Faiss index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)
        
        print(f"Loaded {len(self.metadata)} documents with embedding dimension {dimension}")

    def load_multiple_data(self, embeddings_dir: Path, metadata_dir: Path) -> None:
        """Load all embeddings and metadata from directories"""
        all_embeddings = []
        all_metadata = []
        
        # Get all npy files from embeddings directory
        embedding_files = sorted(embeddings_dir.glob("*.npy"))
        metadata_files = sorted(metadata_dir.glob("*.json"))
        
        for emb_file, meta_file in zip(embedding_files, metadata_files):
            # Load embeddings
            embeddings = np.load(emb_file)
            all_embeddings.append(embeddings)
            
            # Load metadata
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
                all_metadata.extend(metadata)
        
        # Concatenate all embeddings
        combined_embeddings = np.vstack(all_embeddings)
        
        # Initialize Faiss index
        dimension = combined_embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(combined_embeddings)
        
        # Store combined metadata
        self.metadata = all_metadata
        
        print(f"Loaded {len(self.metadata)} total documents from {len(embedding_files)} files")
        print(f"Embedding dimension: {dimension}")
    
    async def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents given a query"""
        # Generate query embedding
        query_embedding = await self.embedding_generator.generate_embedding(query)
        query_embedding = query_embedding.reshape(1, -1)  # Reshape to 2D array
        
        # Search in Faiss index
        distances, indices = self.index.search(query_embedding, k)
        
        # Get corresponding metadata
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            result = {
                "metadata": self.metadata[idx],
                "distance": float(distance)
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
    
    # Define base paths
    embeddings_dir = Path("data/embeddings")
    metadata_dir = Path("data/processed/metadata")
    
    # Load all data
    retriever.load_multiple_data(embeddings_dir, metadata_dir)
    return retriever

# Usage example
async def example_usage():
    retriever = await create_retriever()
    
    # Example search
    query = "What were the Apple's Q2 revenue expectations?"
    results = await retriever.search_similar(query, k=3)
    
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        pprint(result['metadata'])
        print(f"Distance: {result['distance']:.4f}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage()) 