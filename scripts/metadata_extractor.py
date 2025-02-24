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
    # Add constants at the top of the class
    SYSTEM_PROMPT = "Extract key business insights and financial information from the given text. Return the insight directly in one sentence without any prefix. If no meaningful business insight can be extracted, return 'NO_INSIGHT'."
    NO_INSIGHT = "NO_INSIGHT"
    MAX_WORKERS = 20

    def __init__(self, transcripts_dir: str = "data/processed/transcripts/", max_files: int = None):
        self.transcripts_dir = Path(transcripts_dir)
        self.transcripts_dir.mkdir(exist_ok=True)
        self.metadata_dir = Path("data/processed/metadata")
        self.metadata_dir.mkdir(exist_ok=True)
        self.company_info = self._load_company_info()
        self.earnings_dates = self._load_earnings_dates()
        self.max_workers = self.MAX_WORKERS
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

    async def _extract_qa_structure(self, content: str) -> Dict:
        """Extract question and answer structure using LLM"""
        prompt = [
            {"role": "system", "content": "Given a section of an earnings call transcript, identify and separate the questions and answers into multiple pairs. Return in JSON format with array of objects, each containing 'question' and 'answer' as simple strings. If there's no clear Q&A structure, return 'NO_QA'."},
            {"role": "user", "content": content}
        ]
        result = await chat_completion(messages=prompt)
        try:
            if result == "NO_QA":
                return None
            return json.loads(result)
        except:
            return None

    async def _extract_knowledge(self, question: str, answer: str) -> str:
        """Extract key knowledge from Q&A using OpenAI"""
        if not question or not answer:
            return None
            
        content = f"Question: {question}\nAnswer: {answer}"
        prompt = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
        result = await chat_completion(messages=prompt)
        return result if result != self.NO_INSIGHT else None

    def _extract_qa_sync(self, content: str) -> Dict:
        """Synchronous version of extract_qa_structure"""
        return asyncio.run(self._extract_qa_structure(content))

    def _extract_knowledge_sync(self, question: str, answer: str) -> str:
        """Synchronous version of extract_knowledge"""
        return asyncio.run(self._extract_knowledge(question, answer))

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

                metadata_filename = f"{file_info['ticker']}_{file_info['year']}_Q{file_info['q']}.json"
                metadata_path = self.metadata_dir / metadata_filename
                
                if metadata_path.exists():
                    print(f"Skipping already processed file: {csv_path.name}")
                    continue

                earnings_key = f"{file_info['ticker'].lower()}_{file_info['year']}_Q{file_info['q']}"
                print(f"\nProcessing file {file_idx}/{len(csv_files)}: {csv_path.name}")
                
                company_row = self.company_info[
                    self.company_info['Ticker'] == file_info['ticker']
                ].iloc[0]
                
                earnings_date = self.earnings_dates.get(earnings_key)
                if not earnings_date:
                    print(f"Warning: No earnings date found for {earnings_key}")
                    continue
                
                df = pd.read_csv(csv_path)
                
                # Group by Operator sections
                operator_indices = df[df['speaker'] == 'Operator'].index
                qa_sections = []
                
                for i in range(len(operator_indices)):
                    start_idx = operator_indices[i]
                    end_idx = operator_indices[i + 1] if i + 1 < len(operator_indices) else len(df)
                    
                    section = df.iloc[start_idx:end_idx]
                    section_text = "\n".join([f"{row['speaker']}: {row['content']}" 
                                            for _, row in section.iterrows()])
                    qa_sections.append(section_text)

                print(f"Found {len(qa_sections)} sections to process")
                
                # First pass: Extract Q&A structure
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    qa_structures = list(executor.map(self._extract_qa_sync, qa_sections))
                qa_structures = [qa for qa in qa_structures if qa]

                print(f"Found {len(qa_structures)} Q&A structures to process")
                print(qa_structures)
                
                file_metadata = []
                for i, qa_struct in enumerate(qa_structures):
                    if qa_struct:
                        for qa_pair in qa_struct:
                            try:
                                result = await self._extract_knowledge(
                                    qa_pair['question'], 
                                    qa_pair['answer']
                                )
                                
                                if result is not None:
                                    metadata = {
                                        "company": company_row['Company'],
                                        "country": company_row['Country'],
                                        "ticker": file_info['ticker'],
                                        "date": earnings_date,
                                        "year": file_info['year'],
                                        "q": file_info['q'],
                                        "sector": company_row['Sector'],
                                        "industry": company_row['Industry'],
                                        "qa_section": i + 1,
                                        "question": qa_pair['question'],
                                        "answer": qa_pair['answer'],
                                        "knowledge": result
                                    }
                                    file_metadata.append(metadata)
                                    total_processed += 1
                            except Exception as e:
                                print(f"Error processing Q&A pair: {str(e)}")
                                continue
                
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