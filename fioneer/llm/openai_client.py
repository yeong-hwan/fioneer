from openai import OpenAI
from fioneer.config import get_settings
from functools import lru_cache
from typing import Literal, List

# Define allowed model types
ModelType = Literal["gpt-3.5-turbo", "gpt-4o-mini"]

@lru_cache()
def get_openai_client() -> OpenAI:
    """
    Returns cached OpenAI client instance
    """
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)

async def chat_completion(
    messages: list[dict],
    model: ModelType = "gpt-3.5-turbo",
    temperature: float = 0.7,
) -> str:
    """
    Sends a chat completion request to OpenAI
    
    Args:
        messages: List of message dictionaries
        model: OpenAI model to use (either "gpt-3.5-turbo" or "gpt-4o-mini")
        temperature: Sampling temperature
    
    Returns:
        Generated response text
    """
    client = get_openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content

async def create_embeddings(
    texts: List[str],
    model: str = "text-embedding-ada-002"
) -> List[List[float]]:
    """
    Creates embeddings for given texts using OpenAI API
    
    Args:
        texts: List of texts to embed
        model: OpenAI embedding model to use
    
    Returns:
        List of embedding vectors
    """
    client = get_openai_client()
    response = client.embeddings.create(
        input=texts,
        model=model
    )
    return [data.embedding for data in response.data]
