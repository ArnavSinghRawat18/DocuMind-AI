"""
Configuration module for DocuMind AI backend.
Loads environment variables and provides application settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Try to find .env in the backend directory first
_backend_dir = Path(__file__).resolve().parent.parent
_env_path = _backend_dir / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=True)
else:
    load_dotenv(override=True)  # Fall back to default behavior


class Settings:
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "documind")
    
    # Collections
    JOBS_COLLECTION: str = "jobs"
    CHUNKS_COLLECTION: str = "code_chunks"
    EMBEDDINGS_COLLECTION: str = "embeddings"
    
    # Git Configuration
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "./data"))
    REPOS_DIR: Path = DATA_DIR / "repos"
    
    # File Processing Configuration
    ALLOWED_EXTENSIONS: set = {".py", ".js", ".ts", ".md"}
    IGNORED_DIRECTORIES: set = {
        ".git", "node_modules", "venv", "__pycache__", 
        "dist", "build", ".venv", "env", ".env",
        ".idea", ".vscode", "coverage", ".pytest_cache"
    }
    
    # Chunking Configuration
    MAX_CHUNK_TOKENS: int = 800
    CHUNK_OVERLAP_LINES: int = 2  # Lines to overlap between chunks
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ==========================================================================
    # Phase 2: Embedding Configuration
    # ==========================================================================
    
    # OpenAI Configuration (deprecated - kept for backward compatibility)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Hugging Face Configuration
    HF_API_KEY: str = os.getenv("HF_API_KEY", "")
    HF_EMBEDDING_MODEL: str = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Embedding Configuration
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
    
    # Use mock embeddings for testing (set to "true" to use random vectors)
    USE_MOCK_EMBEDDINGS: bool = os.getenv("USE_MOCK_EMBEDDINGS", "true").lower() == "true"
    
    # Vector Search Configuration
    VECTOR_SEARCH_INDEX_NAME: str = "vector_index"
    DEFAULT_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
    
    def __init__(self):
        """Initialize settings and create necessary directories."""
        self.REPOS_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

