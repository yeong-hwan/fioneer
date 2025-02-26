from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    ninja_api_key: str = Field(..., env='NINJA_API_KEY')
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')
    hf_write_token: str = Field(..., env='HF_WRITE_TOKEN')
    hf_read_token: str = Field(..., env='HF_READ_TOKEN')

@lru_cache()
def get_settings():
    return Settings() 