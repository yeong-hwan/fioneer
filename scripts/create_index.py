import faiss
import numpy as np
from pathlib import Path
import json
from typing import List, Dict

def load_metadata_and_embeddings(metadata_dir: Path, embeddings_dir: Path):
    """Load metadata and embeddings"""
    all_metadata = []
    all_embeddings = []
    
    # Process all metadata files
    for metadata_file in sorted(metadata_dir.glob("*.json")):
        # Load metadata
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
            all_metadata.extend(metadata)
        
        # Find corresponding embedding file
        embedding_file = embeddings_dir / f"{metadata_file.stem}.npy"
        if embedding_file.exists():
            embeddings = np.load(str(embedding_file))
            all_embeddings.append(embeddings)
    
    # Combine all embeddings
    final_embeddings = np.vstack(all_embeddings)
    return all_metadata, final_embeddings

def create_and_save_index(embeddings: np.ndarray, metadata: List[Dict], output_dir: Path):
    """Create and save FAISS index"""
    # Check embedding dimension
    dimension = embeddings.shape[1]
    
    # Create IndexFlatIP for L2 normalized inner product similarity
    index = faiss.IndexFlatIP(dimension)
    
    # Normalize embeddings
    faiss.normalize_L2(embeddings)
    
    # Add vectors to index
    index.add(embeddings)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save FAISS index
    faiss.write_index(index, str(output_dir / "earnings.index"))
    
    # Save metadata
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

def main():
    # 디렉토리 설정
    metadata_dir = Path("data/processed/metadata")
    embeddings_dir = Path("data/embeddings")
    output_dir = Path("data/index")
    
    print("Loading metadata and embeddings...")
    metadata, embeddings = load_metadata_and_embeddings(metadata_dir, embeddings_dir)
    
    print(f"Creating index with {len(metadata)} documents...")
    create_and_save_index(embeddings, metadata, output_dir)
    
    print("Done!")

if __name__ == "__main__":
    main() 