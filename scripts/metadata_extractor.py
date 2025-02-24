import json
import pandas as pd
from pathlib import Path
from typing import Dict, List
from fioneer.llm.openai_client import chat_completion
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint

class MetadataExtractor:
    # Add constants at the top of the class
    SYSTEM_PROMPT = "Extract key business insights and financial information from the given text. Return the insight directly in one sentence without any prefix. If no meaningful business insight can be extracted, return 'NO_INSIGHT'."
    NO_INSIGHT = "NO_INSIGHT"
    MAX_WORKERS = 50

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
            {"role": "system", "content": """Given a section of an earnings call transcript, identify and separate the question and answer. 
            If there are multiple distinct questions or points within the same section, split them into separate Q&A pairs.
            Return in JSON format as a list of Q&A pairs, where each pair has:
            - 'question': the full question text
            - 'answer': the full answer text
            - 'q_speaker': the EXACT full name of the person asking the question
            - 'a_speaker': the EXACT full name of the person answering
            
            You must include the FULL NAME of speakers. If a speaker's full name is not provided, mark as 'Analyst'.
            
            Format: {"qa_pairs": [{"question": "...", "answer": "...", "q_speaker": "...", "a_speaker": "..."}]}
            If there's no clear Q&A structure, return 'NO_QA'."""},
            {"role": "user", "content": content}
        ]
        result = await chat_completion(messages=prompt)
        try:
            if result == "NO_QA":
                return None
            qa_dict = json.loads(result)
            qa_pairs = qa_dict.get('qa_pairs', [])
            
            # Validate speaker names
            for qa in qa_pairs:
                if not qa.get('a_speaker'):
                    qa['a_speaker'] = 'UNKNOWN_SPEAKER'
            
            return qa_pairs
        except:
            return None

    async def _extract_insight(self, question: str, answer: str) -> Dict:
        """Extract key insight and reasoning steps from Q&A using OpenAI"""
        content = f"Question: {question}\nAnswer: {answer}"
        prompt = [
            {"role": "system", "content": """Analyze this Q&A from an earnings call. 
            First, provide your step-by-step factual reasoning process, focusing on the key business facts and numbers mentioned.
            Exclude any speaker information or subjective interpretations.
            Number each reasoning step (1., 2., etc.).
            Then, extract the key business insight.
            
            Return in JSON format:
            {
                "reasoning_steps": ["1. fact1", "2. fact2", "3. fact3"],
                "insight": "final insight"
            }
            
            If no meaningful insight can be extracted, return 'NO_INSIGHT'."""},
            {"role": "user", "content": content}
        ]
        result = await chat_completion(messages=prompt)
        
        if result == self.NO_INSIGHT:
            return None
            
        try:
            result_dict = json.loads(result)
            return result_dict
        except:
            return None

    def _extract_qa_sync(self, content: str) -> Dict:
        """Synchronous version of extract_qa_structure"""
        return asyncio.run(self._extract_qa_structure(content))

    def _extract_insight_sync(self, question: str, answer: str) -> str:
        """Synchronous version of extract_insight"""
        return asyncio.run(self._extract_insight(question, answer))

    async def _summarize_question(self, question: str) -> str:
        """Summarize the question into a concise form"""
        prompt = [
            {"role": "system", "content": "Summarize this earnings call question into a brief, clear form while maintaining the key points. Return only the summarized question."},
            {"role": "user", "content": question}
        ]
        return await chat_completion(messages=prompt)

    def _summarize_question_sync(self, question: str) -> str:
        """Synchronous version of summarize_question"""
        return asyncio.run(self._summarize_question(question))

    async def _summarize_answer(self, answer: str) -> str:
        """Summarize the answer into a concise form"""
        prompt = [
            {"role": "system", "content": "Summarize this earnings call answer into a brief, clear form while maintaining the key points. Return only the summarized answer."},
            {"role": "user", "content": answer}
        ]
        return await chat_completion(messages=prompt)

    def _summarize_answer_sync(self, answer: str) -> str:
        """Synchronous version of summarize_answer"""
        return asyncio.run(self._summarize_answer(answer))

    async def _process_qa_batch(self, qa_pairs: List[Dict]) -> List[Dict]:
        """Process a batch of Q&A pairs in parallel"""
        async def process_single_qa(qa: Dict):
            if not (qa.get('question') and qa.get('answer')):
                return None
            
            # Run all tasks in parallel
            insight_task = self._extract_insight(qa['question'], qa['answer'])
            question_summary_task = self._summarize_question(qa['question'])
            answer_summary_task = self._summarize_answer(qa['answer'])
            
            insight, q_summary, a_summary = await asyncio.gather(
                insight_task, 
                question_summary_task,
                answer_summary_task
            )
            
            if insight is None:
                return None
                
            return {
                'q_speaker': qa.get('q_speaker'),
                'a_speaker': qa.get('a_speaker'),
                'question': q_summary,
                'question_full': qa['question'],
                'answer': a_summary,
                'answer_full': qa['answer'],
                'insight': insight
            }

    async def extract_metadata(self) -> List[Dict]:
        """Extract metadata from all CSV files in transcripts directory"""
        total_processed = 0
        skipped_qa = 0
        skipped_insights = 0

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
                
                # Print skipped Q&A sections
                skipped_sections = [
                    (i, section) for i, (qa, section) in enumerate(zip(qa_structures, qa_sections))
                    if not qa
                ]
                if skipped_sections:
                    print("\nSkipped Q&A sections:")
                    for i, section in skipped_sections:
                        print(f"\nSection {i}:")
                        pprint(section)
                    skipped_qa += len(skipped_sections)
                
                qa_structures = [qa for qa in qa_structures if qa]
                print(f"Found {len(qa_structures)} Q&A structures to process")
                
                # Prepare all Q&A pairs for insight extraction
                insight_tasks = []
                qa_pairs_info = []  # Store Q&A pairs with speaker info
                for qa_structure in qa_structures:
                    for qa_pair in qa_structure:
                        question = qa_pair.get('question')
                        answer = qa_pair.get('answer')
                        if question and answer:
                            insight_tasks.append((question, answer))
                            qa_pairs_info.append({
                                'q_speaker': qa_pair.get('q_speaker'),
                                'a_speaker': qa_pair.get('a_speaker')
                            })

                # Second pass: Extract insights and summarize Q&A in parallel
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    insight_results = list(executor.map(
                        lambda x: self._extract_insight_sync(x[0], x[1]), 
                        insight_tasks
                    ))
                    question_summaries = list(executor.map(
                        lambda x: self._summarize_question_sync(x[0]),
                        insight_tasks
                    ))
                    answer_summaries = list(executor.map(
                        lambda x: self._summarize_answer_sync(x[1]),
                        insight_tasks
                    ))

                file_metadata = []
                for (question, answer), result, q_summary, a_summary, speakers in zip(
                    insight_tasks, insight_results, question_summaries, answer_summaries, qa_pairs_info
                ):
                    if result is None:
                        print("\nSkipped insight extraction:")
                        pprint({"question": question, "answer": answer})
                        skipped_insights += 1
                        continue
                        
                    metadata = {
                        "company": company_row['Company'],
                        "country": company_row['Country'],
                        "ticker": file_info['ticker'],
                        "date": earnings_date,
                        "year": file_info['year'],
                        "q": file_info['q'],
                        "sector": company_row['Sector'],
                        "industry": company_row['Industry'],
                        "q_speaker": speakers['q_speaker'],
                        "a_speaker": speakers['a_speaker'],
                        "question_summary": q_summary,
                        "answer_summary": a_summary,
                        "insight": result["insight"],
                        "reasoning_steps": result["reasoning_steps"]
                    }
                    file_metadata.append(metadata)
                    total_processed += 1

                self.save_metadata(file_metadata, metadata_path)
                print(f"Completed processing {csv_path.name} and saved metadata")
                    
            except Exception as e:
                print(f"Error processing {csv_path}: {str(e)}")
                continue

        print(f"\nProcessing Summary:")
        print(f"Total processed: {total_processed} entries")
        print(f"Skipped Q&A sections: {skipped_qa}")
        print(f"Skipped insight extractions: {skipped_insights}")
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