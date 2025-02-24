from typing import List, Dict, Any
import numpy as np
from fioneer.llm.openai_client import create_embeddings

class EmbeddingGenerator:
    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model
    
    async def generate_embedding(self, metadata: List[Dict[str, Any]]) -> np.ndarray:
        """Convert metadata to embeddings suitable for Faiss"""
        try:
            texts = []
            for item in metadata:
                text_parts = []
                
                # Company and market info
                text_parts.append(f"Company: {item.get('company', '')}")
                text_parts.append(f"Country: {item.get('country', '')}")
                text_parts.append(f"Ticker: {item.get('ticker', '')}")
                text_parts.append(f"Date: {item.get('date', '')}")
                text_parts.append(f"Year: {item.get('year', '')}")
                text_parts.append(f"Quarter: {item.get('q', '')}")
                text_parts.append(f"Sector: {item.get('sector', '')}")
                text_parts.append(f"Industry: {item.get('industry', '')}")
                
                # Q&A participants
                text_parts.append(f"Question Speaker: {item.get('q_speaker', '')}")
                text_parts.append(f"Answer Speaker: {item.get('a_speaker', '')}")
                
                # Q&A content
                text_parts.append(f"Question Summary: {item.get('question_summary', '')}")
                text_parts.append(f"Answer Summary: {item.get('answer_summary', '')}")
                text_parts.append(f"Insight: {item.get('insight', '')}")
                
                # Reasoning steps
                if "reasoning_steps" in item and item['reasoning_steps']:
                    steps = " ".join(item['reasoning_steps'])
                    text_parts.append(f"Reasoning Steps: {steps}")
                
                # Filter out empty strings and join
                text = " ".join(part for part in text_parts if part.split(": ")[1])
                texts.append(text)
            
            # Generate embeddings and convert to float32 numpy array
            embeddings = await create_embeddings(texts, self.model)
            return np.array(embeddings, dtype=np.float32)
            
        except Exception as e:
            raise ValueError(f"Failed to generate embeddings: {e}")
