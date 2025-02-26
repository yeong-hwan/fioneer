from huggingface_hub import HfApi
from pathlib import Path
from fioneer.config import get_settings
import logging
from tqdm import tqdm

def upload_to_hf():
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Get token from settings
    settings = get_settings()
    
    # Initialize API with token
    api = HfApi(token=settings.hf_token)
    REPO_ID = "yeong-hwan/fioneer-data"
    
    # Try to create repository, continue if it already exists
    try:
        api.create_repo(
            repo_id=REPO_ID,
            repo_type="dataset",
            private=False
        )
    except Exception as e:
        logger.info(f"Repository already exists or other error occurred: {e}")
    
    # Upload configuration
    CHUNK_SIZE = 50  # Number of files to upload in each chunk
    
    # Define paths
    paths_to_upload = [
        ("data/embeddings", "embeddings"),
        ("data/processed/metadata", "metadata")
    ]
    
    # Upload each directory
    for local_dir, repo_dir in paths_to_upload:
        logger.info(f"\nUploading {local_dir} to {repo_dir}")
        
        # Get all files in directory
        files = list(Path(local_dir).rglob("*"))
        files = [f for f in files if f.is_file()]
        
        # Upload in chunks with progress bar
        for i in tqdm(range(0, len(files), CHUNK_SIZE), desc=f"Uploading {repo_dir}"):
            chunk = files[i:i + CHUNK_SIZE]
            try:
                api.upload_folder(
                    folder_path=local_dir,
                    path_in_repo=repo_dir,
                    repo_id=REPO_ID,
                    repo_type="dataset",
                    allow_patterns=[str(f.relative_to(local_dir)) for f in chunk],
                    delete_patterns=None,  # Don't delete existing files
                )
                logger.info(f"Successfully uploaded chunk {i//CHUNK_SIZE + 1}")
            except Exception as e:
                logger.error(f"Error uploading chunk {i//CHUNK_SIZE + 1}: {e}")
                continue

if __name__ == "__main__":
    upload_to_hf() 