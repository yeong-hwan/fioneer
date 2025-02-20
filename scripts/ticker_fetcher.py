import yfinance as yf
import json
import pandas as pd

def get_top_tickers(top_count):
    """
    Get top 100 US stocks by market cap using yfinance
    """
    # Download ^SPX (S&P 500) components
    sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    print(sp500)
    tickers = sp500['Symbol'].tolist()
    
    # return top tickers
    return tickers[:top_count]

def save_tickers_to_json(tickers):
    with open('datasets/ticker_list.json', 'w') as f:
        json.dump(tickers, f, indent=4)

def main():
    print("Fetching top 100 US stocks by market cap...")
    TOP_COUNT = 500
    tickers = get_top_tickers(TOP_COUNT)
    print(f"Found {len(tickers)} tickers")
    
    save_tickers_to_json(tickers)
    print("JSON file saved")

if __name__ == "__main__":
    main()
