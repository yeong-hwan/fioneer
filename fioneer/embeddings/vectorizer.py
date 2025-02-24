from typing import List, Dict, Any
import numpy as np
from fioneer.llm.openai_client import create_embeddings
import json
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class EmbeddingGenerator:
    def __init__(self, model: str = "text-embedding-ada-002", batch_size: int = 20):
        self.model = model
        self.batch_size = batch_size
    
    def format_text(self, text: Dict) -> str:
        """Format dictionary into a single string"""
        return f"""
Company: {text['company']}
Country: {text['country']}
Ticker: {text['ticker']}
Date: {text['date']}
Year: {text['year']}
Quarter: {text['q']}
Sector: {text['sector']}
Industry: {text['industry']}
Question Speaker: {text['q_speaker']}
Answer Speaker: {text['a_speaker']}
Question Summary: {text['question_summary']}
Answer Summary: {text['answer_summary']}
Insight: {text['insight']}
Reasoning Steps: {' '.join(text['reasoning_steps'])}
"""

    async def generate_embeddings_batch(self, items: List[Dict]) -> np.ndarray:
        """Generate embeddings for a batch of items"""
        if not items:
            return np.array([])
            
        try:
            texts = [self.format_text(item) for item in items]
            response = await create_embeddings(texts, self.model)
            embeddings = np.array(response, dtype=np.float32)
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings for batch: {e}")
            return np.array([])

    async def process_items(self, items: List[Dict], desc: str = "") -> np.ndarray:
        """Process items in batches"""
        if not items:
            raise ValueError("No items to process")
            
        all_embeddings = []
        
        # Split items into batches
        for i in tqdm(range(0, len(items), self.batch_size), desc=desc):
            batch = items[i:i + self.batch_size]
            batch_embeddings = await self.generate_embeddings_batch(batch)
            if batch_embeddings.size > 0:
                all_embeddings.append(batch_embeddings)
        
        if not all_embeddings:
            raise ValueError("Failed to generate any embeddings")
            
        return np.vstack(all_embeddings)

    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text query"""
        try:
            response = await create_embeddings([text], self.model)
            return np.array(response, dtype=np.float32)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise

async def generate_and_save_embeddings():
    # Get all JSON files from metadata directory
    metadata_dir = Path("data/processed/metadata")
    embeddings_dir = Path("data/embeddings")
    embeddings_dir.mkdir(exist_ok=True)
    
    # Get and sort JSON files
    json_files = sorted(metadata_dir.glob("*.json"))
    
    if not json_files:
        print("No JSON files found in metadata directory")
        return
    
    # Initialize embedding generator
    generator = EmbeddingGenerator()
    
    # Process each file sequentially with batch processing
    for json_path in json_files:
        output_path = embeddings_dir / f"{json_path.stem}.npy"
        
        if output_path.exists():
            print(f"Skipping {json_path.name} - embeddings already exist")
            continue
            
        print(f"\nProcessing {json_path.name}...")
        
        try:
            # Load JSON data
            with open(json_path, "r") as f:
                metadata = json.load(f)
            
            if not metadata:
                print(f"Skipping {json_path.name} - empty file")
                continue
            
            # Process items in batches
            embeddings = await generator.process_items(
                metadata,
                desc=f"Generating embeddings for {json_path.name}"
            )
            
            # Save embeddings
            np.save(output_path, embeddings)
            
            print(f"Embeddings saved to {output_path}")
            print(f"Embeddings shape: {embeddings.shape}")
            
        except Exception as e:
            print(f"Error processing {json_path.name}: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(generate_and_save_embeddings())
