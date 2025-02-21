import json
import yfinance as yf
from typing import List
import pandas as pd
from tqdm import tqdm

def load_tickers() -> List[str]:
    with open('datasets/ticker_list.json', 'r') as f:
        return json.load(f)

def get_sector_industry_info():
    tickers = load_tickers()
    results = []
    
    # tqdm으로 진행률 표시
    for ticker in tqdm(tickers, desc="Fetching sector/industry info"):
        try:
            # BRK.B와 같은 특수한 티커 처리
            ticker_formatted = ticker.replace('.', '-')
            stock = yf.Ticker(ticker_formatted)
            info = stock.info
            
            results.append({
                'Ticker': ticker,
                'Sector': info.get('sector', 'N/A'),
                'Industry': info.get('industry', 'N/A')
            })
            
        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")
            continue
    
    # DataFrame으로 변환하여 깔끔하게 출력
    df = pd.DataFrame(results)
    return df

if __name__ == "__main__":
    df = get_sector_industry_info()
    print("\nSector and Industry Information:")
    print(df.to_string(index=False))
    
    # CSV로 저장 (선택사항)
    df.to_csv('data/processed/sector_industry_info.csv', index=False)
