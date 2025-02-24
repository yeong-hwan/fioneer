import json
import glob
import os
import csv
from typing import List, Dict

def process_transcripts(directory: str) -> List[Dict]:
    """
    Process all transcript files in the directory to create an integrated dataset
    File name format: {ticker}_{year}_{q}.txt
    """
    dataset = []
    
    # Search all transcript files
    for file_path in glob.glob(os.path.join(directory, "*.csv")):
        # Extract information from filename
        filename = os.path.basename(file_path).replace(".csv", "")
        ticker, year, q = filename.split("_")
        
        conversations = []
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                conversations.append({
                    "speaker": row["speaker"],
                    "content": row["content"]
                })
        
        # Add to dataset if there are conversations
        if conversations:
            dataset.append({
                "ticker": ticker,
                "year": int(year),  # Convert to int for proper sorting
                "q": int(q.replace('Q', '')),  # Remove 'Q' and convert to int
                "conversations": conversations
            })
    
    # Sort by year (desc), ticker (asc), quarter (desc)
    dataset.sort(key=lambda x: (-x["year"], x["ticker"], -x["q"]))
    
    return dataset

def save_to_jsonl(dataset: List[Dict], output_file: str):
    """
    Save dataset in JSONL format
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    transcripts_dir = "data/processed/transcripts"
    output_file = "data/2024-earnings-call-transcripts.jsonl"
    
    dataset = process_transcripts(transcripts_dir)
    save_to_jsonl(dataset, output_file)
    print(f"Dataset has been saved to {output_file}")