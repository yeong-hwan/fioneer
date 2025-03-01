import sys
import argparse
from fioneer.ninjas.ninjas_client import NinjasClient
from pprint import pprint
import pandas as pd

def fetch_earnings_call(ticker: str, year: int, quarter: int):
    """Fetch a single earnings call transcript"""
    try:
        client = NinjasClient()
        result = client.get_earnings_transcript(ticker, year, quarter)
        
        # Print basic information
        print(f"\n{'='*50}")
        print(f"Earnings Call Transcript for {ticker.upper()}")
        print(f"Year: {year}, Quarter: {quarter}")
        print(f"{'='*50}\n")

        # Print the transcript content
        if result.get('title'):
            print(f"Title: {result['title']}\n")
        
        if result.get('date'):
            print(f"Date: {result['date']}\n")
            
        if result.get('transcript'):
            print("Transcript:")
            # Convert transcript to DataFrame with separate columns for speaker and content
            lines = result['transcript'].split('\n')
            processed_data = []
            
            for line in lines:
                # Split by first colon to separate speaker and content
                parts = line.split(':', 1)
                if len(parts) == 2:
                    speaker = parts[0].strip()
                    content = parts[1].strip()
                    processed_data.append({'speaker': speaker, 'content': content})
                
            df = pd.DataFrame(processed_data)
            print(df)
        else:
            print("No transcript content available")
            
    except Exception as e:
        print(f"Error fetching transcript: {str(e)}")
        sys.exit(1)

def main():
    # Use hardcoded values instead of command line arguments
    ticker = "aapl"
    year = 2024
    quarter = 4
    
    fetch_earnings_call(ticker, year, quarter)

if __name__ == "__main__":
    main() 