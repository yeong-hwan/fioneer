from typing import List
import openai
import numpy as np
from fioneer.config import get_settings

# Configure OpenAI API key
settings = get_settings()
openai.api_key = settings.openai_api_key

class EmbeddingGenerator:
    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model

    def generate_embedding(self, transcripts: List[str]) -> np.ndarray:
        """Convert transcripts to embeddings using OpenAI API"""
        try:
            response = openai.Embedding.create(
                input=transcripts,
                model=self.model
            )
            embeddings = [data["embedding"] for data in response["data"]]
            return np.array(embeddings)
        except Exception as e:
            raise ValueError(f"Failed to generate embeddings: {e}")
