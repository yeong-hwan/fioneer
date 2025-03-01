import json
import yfinance as yf
from typing import List
import pandas as pd
from tqdm import tqdm

def load_tickers() -> List[str]:
    with open('data/processed/ticker_list.json', 'r') as f:
        return json.load(f)

def get_company_info():
    tickers = load_tickers()
    results = []
    
    # Show progress with tqdm
    for ticker in tqdm(tickers, desc="Fetching company info"):
        try:
            # Handle special tickers like BRK.B
            ticker_formatted = ticker.replace('.', '-')
            stock = yf.Ticker(ticker_formatted)
            info = stock.info
            
            results.append({
                'Ticker': ticker,
                'Company': info.get('longName', 'N/A'),
                'Country': info.get('country', 'N/A'),
                'Sector': info.get('sector', 'N/A'),
                'Industry': info.get('industry', 'N/A')
            })
            
        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")
            continue
    
    # Convert to DataFrame for clean output
    df = pd.DataFrame(results)
    return df

if __name__ == "__main__":
    df = get_company_info()
    print("\nCompany Information:")
    print(df.to_string(index=False))
    
    # Save to CSV (optional)
    df.to_csv('data/processed/company_info.csv', index=False)
