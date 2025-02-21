import pandas as pd
from fioneer.ninjas.ninjas_client import NinjasClient
import json
import os

def parse_earnings_call(transcript):
    """
    split the earnings call transcript into speaker and content
    """

    # split by newline
    lines = transcript.split('\n')
    
    # remove empty lines and trim whitespace
    lines = [line.strip() for line in lines if line.strip()]
    
    # split each line into speaker and content
    parsed_data = []
    for line in lines:
        # split by ':'
        parts = line.split(':', 1)  # split only once
        if len(parts) == 2:
            speaker = parts[0].strip()
            content = parts[1].strip()
            parsed_data.append({
                "speaker": speaker,
                "content": content
            })
        else:
            # if ':' is not found, save the whole line as content
            parsed_data.append({
                "speaker": "",
                "content": line
            })
    
    return parsed_data

def save_earnings_transcript_to_csv(symbol: str, year: int, quarter: int) -> tuple[str, dict]:
    print(f"\nProcessing earnings call for {symbol} {year} Q{quarter}\n")
    
    # Initialize client
    client = NinjasClient()
    
    # Get transcript data
    transcript_data = client.get_earnings_transcript(symbol, year, quarter)
    
    # Parse the transcript
    parsed_data = parse_earnings_call(transcript_data["transcript"])
    
    # Create DataFrame
    df = pd.DataFrame(parsed_data)
    
    # Display DataFrame preview
    print(df)
    
    # Generate filename with datasets path
    csv_filename = f"data/processed/transcripts/{symbol.lower()}_{year}_Q{quarter}.csv"
    
    # Save to CSV
    df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"\nSaved to file: {csv_filename}")
    
    # Return date information
    date_info = {
        "symbol": symbol,
        "year": year,
        "quarter": quarter,
        "date": transcript_data.get("date", "")
    }
    
    return csv_filename, date_info

def process_all_tickers():
    """
    Process earnings calls for all tickers in the ticker list for the last 10 years
    """
    # Read ticker list
    with open('data/processed/ticker_list.json', 'r') as f:
        tickers = json.load(f)
    
    # Create directory for CSV files if it doesn't exist
    os.makedirs('data/processed/transcripts', exist_ok=True)
    
    # Set year range and quarters
    CURRENT_YEAR = 2024
    YEARS = range(CURRENT_YEAR, CURRENT_YEAR - 1, -1)  # 2024 to 2015
    QUARTERS = range(1, 5)  # 1, 2, 3, 4
    
    # Dictionary to store date information with filename as key
    dates_dict = {}
    
    # Process each ticker
    for ticker in tickers:
        # Process each year and quarter
        for year in YEARS:
            for quarter in QUARTERS:
                try:
                    filename, date_info = save_earnings_transcript_to_csv(ticker, year, quarter)
                    # Create key from filename (basename without extension)
                    key = os.path.splitext(os.path.basename(filename))[0]
                    dates_dict[key] = date_info["date"]
                except Exception as e:
                    print(f"Error processing {ticker} {year} Q{quarter}: {str(e)}")
                    continue
    
    # Save date information to JSON file
    dates_filename = 'data/processed/earnings_dates.json'
    with open(dates_filename, 'w') as f:
        json.dump(dates_dict, f, indent=4)
    print(f"\nSaved all dates to: {dates_filename}")

if __name__ == "__main__":
    process_all_tickers()
