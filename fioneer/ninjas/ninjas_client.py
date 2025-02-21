import os
import requests
from dotenv import load_dotenv
from fioneer.config import get_settings

class NinjasClient:
    BASE_URL = "https://api.api-ninjas.com/v1"

    def __init__(self):
        settings = get_settings()
        self.ninja_api_key = settings.ninja_api_key
        if not self.ninja_api_key:
            raise ValueError("Ninja API Key is not set")

    def get_earnings_transcript(self, symbol: str, year: int, quarter: int):
        url = f"{self.BASE_URL}/earningstranscript"
        params = {
            "ticker": symbol,
            "year": year,
            "quarter": quarter
        }
        headers = {
            "X-Api-Key": self.ninja_api_key
        }
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()