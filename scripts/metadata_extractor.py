import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List
from fioneer.llm.openai_client import chat_completion
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

class MetadataExtractor:
    def __init__(self, transcripts_dir: str = "data/processed/transcripts/", max_files: int = None):
        self.transcripts_dir = Path(transcripts_dir)
        self.transcripts_dir.mkdir(exist_ok=True)
        self.metadata_dir = Path("data/processed/metadata")
        self.metadata_dir.mkdir(exist_ok=True)
        self.company_info = self._load_company_info()
        self.earnings_dates = self._load_earnings_dates()
        self.max_workers = 20
        self.max_files = max_files

    def _load_company_info(self) -> pd.DataFrame:
        """Load company information from CSV file"""
        company_info_path = Path("data/processed/company_info.csv")
        return pd.read_csv(company_info_path)

    def _load_earnings_dates(self) -> Dict:
        """Load earnings dates from JSON file"""
        earnings_dates_path = Path("data/processed/earnings_dates.json")
        with open(earnings_dates_path, 'r') as f:
            return json.load(f)

    def _parse_filename(self, filename: str) -> Dict:
        """Extract ticker, year and quarter from filename"""
        try:
            # Example: a_2024_Q1 -> {'ticker': 'A', 'year': 2024, 'q': 1}
            parts = filename.split('_')
            if len(parts) != 3 or not parts[1].isdigit() or not parts[2].startswith('Q'):
                print(f"Skipping invalid filename format: {filename}")
                return None
            
            return {
                'ticker': parts[0].upper(),
                'year': int(parts[1]),
                'q': int(parts[2][1])
            }
        except Exception as e:
            print(f"Error parsing filename {filename}: {str(e)}")
            return None

    async def _extract_knowledge(self, content: str) -> str:
        """Extract key knowledge from content using OpenAI"""
        prompt = [
            {"role": "system", "content": "Extract key business insights and financial information from the given text. Return the insight like analyst report in one sentence. If no meaningful business insight can be extracted, return 'NO_INSIGHT'."},
            {"role": "user", "content": content}
        ]
        result = await chat_completion(messages=prompt)
        return result if result != "NO_INSIGHT" else None

    def _extract_knowledge_sync(self, content: str) -> str:
        """Synchronous version of extract_knowledge"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._extract_knowledge(content))
            return result
        finally:
            loop.close()

    async def extract_metadata(self) -> List[Dict]:
        """Extract metadata from all CSV files in transcripts directory"""
        total_processed = 0

        csv_files = sorted(self.transcripts_dir.glob("*.csv"))
        if self.max_files:
            csv_files = csv_files[:self.max_files]
            print(f"Processing limited to {self.max_files} files")
        print(f"Found {len(csv_files)} CSV files in {self.transcripts_dir}")
        
        for file_idx, csv_path in enumerate(csv_files, 1):
            try:
                file_info = self._parse_filename(csv_path.stem)
                if not file_info:
                    continue

                # Generate metadata filename
                metadata_filename = f"{file_info['ticker']}_{file_info['year']}_Q{file_info['q']}.json"
                metadata_path = self.metadata_dir / metadata_filename
                
                # Skip if file already exists
                if metadata_path.exists():
                    print(f"Skipping already processed file: {csv_path.name}")
                    continue

                earnings_key = f"{file_info['ticker'].lower()}_{file_info['year']}_Q{file_info['q']}"
                print(f"\nProcessing file {file_idx}/{len(csv_files)}: {csv_path.name} (earnings_key: {earnings_key})")
                
                company_row = self.company_info[
                    self.company_info['Ticker'] == file_info['ticker']
                ].iloc[0]
                
                earnings_date = self.earnings_dates.get(earnings_key)
                if not earnings_date:
                    print(f"Warning: No earnings date found for {earnings_key}")
                    continue
                
                df = pd.read_csv(csv_path)
                total_rows = len(df)
                print(f"Found {total_rows} rows to process")
                
                print("Processing utterances...")
                filtered_df = df[df['speaker'] != 'Operator']
                contents = filtered_df['content'].tolist()
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    results = list(executor.map(self._extract_knowledge_sync, contents))
                    
                print("Creating metadata entries...")
                file_metadata = []
                for i, (_, row) in enumerate(filtered_df.iterrows()):
                    if results[i] is not None:
                        metadata = {
                            "company": company_row['Company'],
                            "country": company_row['Country'],
                            "ticker": file_info['ticker'],
                            "date": earnings_date,
                            "year": file_info['year'],
                            "q": file_info['q'],
                            "sector": company_row['Sector'],
                            "industry": company_row['Industry'],
                            "speaker": row['speaker'],
                            "knowledge": results[i]
                        }
                        file_metadata.append(metadata)
                        total_processed += 1
                    
                    if total_processed % 5 == 0:
                        print(f"Progress: {total_processed}/{total_rows} utterances processed")
                
                # Save metadata for current file
                self.save_metadata(file_metadata, metadata_path)
                print(f"Completed processing {csv_path.name} and saved metadata")
                    
            except Exception as e:
                print(f"Error processing {csv_path}: {str(e)}")
                continue

        print(f"\nTotal processed: {total_processed} entries from {len(csv_files)} files")
        return total_processed

    def save_metadata(self, metadata_list: List[Dict], metadata_path: Path) -> None:
        """Save metadata to individual JSON file"""
        # Create backup of existing file if it exists
        if metadata_path.exists():
            backup_file = metadata_path.with_suffix('.json.bak')
            metadata_path.rename(backup_file)
            
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_list, f, indent=2, ensure_ascii=False)
            # Remove backup file after successful save
            backup_file = metadata_path.with_suffix('.json.bak')
            if backup_file.exists():
                backup_file.unlink()
        except Exception as e:
            # Restore from backup if save fails
            if backup_file.exists():
                backup_file.rename(metadata_path)
            raise e

    async def process(self) -> None:
        """Extract and save metadata"""
        total_processed = await self.extract_metadata()
        print(f"Processed {total_processed} entries")

async def main():
    # Example: Process only 5 files
    extractor = MetadataExtractor(max_files=2)  # Remove or set to None to process all files
    await extractor.process()

if __name__ == "__main__":
    asyncio.run(main())