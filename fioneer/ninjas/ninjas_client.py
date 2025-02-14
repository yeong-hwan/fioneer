import os
import requests
from dotenv import load_dotenv

load_dotenv()

class NinjasClient:
    BASE_URL = "https://api.api-ninjas.com/v1"

    def __init__(self):
        self.api_key = os.getenv("FINNHUB_API_KEY")
        self.ninja_api_key = os.getenv("NINJA_API_KEY")
        if not self.api_key:
            raise ValueError("Finnhub API Key가 설정되지 않았습니다. .env 파일을 확인하세요.")
        if not self.ninja_api_key:
            raise ValueError("Ninja API Key가 설정되지 않았습니다. .env 파일을 확인하세요.")

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