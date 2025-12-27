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
    
    # ==========================================================================
    # MongoDB Configuration
    # ==========================================================================
    MONGODB_URI: str = os.getenv("MONGODB_URI", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "documind")
    
    # Collections
    JOBS_COLLECTION: str = "jobs"
    CHUNKS_COLLECTION: str = "code_chunks"
    EMBEDDINGS_COLLECTION: str = "embeddings"
    
    # ==========================================================================
    # Git Configuration
    # ==========================================================================
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "./data"))
    REPOS_DIR: Path = DATA_DIR / "repos"
    
    # ==========================================================================
    # File Processing Configuration
    # ==========================================================================
    ALLOWED_EXTENSIONS: set = {".py", ".js", ".ts", ".md", ".jsx", ".tsx", ".java", ".go", ".rs"}
    IGNORED_DIRECTORIES: set = {
        ".git", "node_modules", "venv", "__pycache__", 
        "dist", "build", ".venv", "env", ".env",
        ".idea", ".vscode", "coverage", ".pytest_cache",
        "target", "vendor", ".tox", ".mypy_cache"
    }
    
    # ==========================================================================
    # Chunking Configuration
    # ==========================================================================
    MAX_CHUNK_TOKENS: int = int(os.getenv("MAX_CHUNK_TOKENS", "800"))
    CHUNK_OVERLAP_LINES: int = int(os.getenv("CHUNK_OVERLAP_LINES", "2"))
    
    # ==========================================================================
    # API Configuration
    # ==========================================================================
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    
    # ==========================================================================
    # Logging
    # ==========================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "colored")  # colored, json, plain
    
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
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
    
    # Use mock embeddings for testing (set to "true" to use random vectors)
    USE_MOCK_EMBEDDINGS: bool = os.getenv("USE_MOCK_EMBEDDINGS", "false").lower() == "true"
    
    # Vector Search Configuration
    VECTOR_SEARCH_INDEX_NAME: str = os.getenv("VECTOR_SEARCH_INDEX_NAME", "vector_index")
    DEFAULT_TOP_K: int = int(os.getenv("DEFAULT_TOP_K", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
    
    # ==========================================================================
    # Phase 3: LLM / Generation Configuration
    # ==========================================================================
    
    # LLM Provider: "ollama", "huggingface", "openai", "mock"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
    
    # Use mock LLM for testing
    USE_MOCK_LLM: bool = os.getenv("USE_MOCK_LLM", "true").lower() == "true"
    
    # Ollama LLM (Local - No API key required)
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3:8b")
    
    # Hugging Face LLM
    HF_LLM_MODEL: str = os.getenv("HF_LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
    
    # OpenAI LLM
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # LLM Request Configuration
    LLM_TIMEOUT: float = float(os.getenv("LLM_TIMEOUT", "60.0"))
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
    LLM_DEFAULT_MAX_TOKENS: int = int(os.getenv("LLM_DEFAULT_MAX_TOKENS", "1024"))
    LLM_DEFAULT_TEMPERATURE: float = float(os.getenv("LLM_DEFAULT_TEMPERATURE", "0.7"))
    
    # Generation Configuration
    MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "3000"))
    
    # ==========================================================================
    # Security Configuration
    # ==========================================================================
    
    # CORS Configuration
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    
    # Input Validation
    MAX_QUERY_LENGTH: int = int(os.getenv("MAX_QUERY_LENGTH", "2000"))
    MAX_REPO_URL_LENGTH: int = int(os.getenv("MAX_REPO_URL_LENGTH", "500"))
    
    # Allowed Git hosts (for security)
    ALLOWED_GIT_HOSTS: set = {
        "github.com",
        "gitlab.com",
        "bitbucket.org",
        os.getenv("CUSTOM_GIT_HOST", "")
    } - {""}  # Remove empty string if CUSTOM_GIT_HOST not set
    
    # ==========================================================================
    # Phase 4: Rate Limiting Configuration
    # ==========================================================================
    
    RATE_LIMIT_INGEST: str = os.getenv("RATE_LIMIT_INGEST", "60/minute")
    RATE_LIMIT_RETRIEVE: str = os.getenv("RATE_LIMIT_RETRIEVE", "60/minute")
    RATE_LIMIT_GENERATE: str = os.getenv("RATE_LIMIT_GENERATE", "30/minute")
    
    # Payload size limits (bytes)
    MAX_REQUEST_BODY_SIZE: int = int(os.getenv("MAX_REQUEST_BODY_SIZE", str(1024 * 1024)))  # 1MB
    MAX_GENERATE_BODY_SIZE: int = int(os.getenv("MAX_GENERATE_BODY_SIZE", str(64 * 1024)))  # 64KB
    
    def __init__(self):
        """Initialize settings and create necessary directories."""
        self.REPOS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Validate critical settings on startup
        self._validate_settings()
    
    def _validate_settings(self):
        """
        Validate configuration settings.
        Fails fast if critical settings are invalid.
        """
        errors = []
        
        # ==========================================================================
        # Critical Settings Validation
        # ==========================================================================
        
        # API port
        if not 1 <= self.API_PORT <= 65535:
            errors.append(f"Invalid API_PORT: {self.API_PORT} (must be 1-65535)")
        
        # MongoDB URI
        if not self.MONGODB_URI or self.MONGODB_URI == "mongodb://localhost:27017":
            if self.is_production():
                errors.append("MONGODB_URI not set for production environment")
        
        # LLM configuration in production
        if self.is_production():
            if self.USE_MOCK_LLM:
                errors.append("USE_MOCK_LLM=true not allowed in production")
            if self.USE_MOCK_EMBEDDINGS:
                errors.append("USE_MOCK_EMBEDDINGS=true not allowed in production")
            if self.LLM_PROVIDER == "mock":
                errors.append("LLM_PROVIDER=mock not allowed in production")
            if not self.HF_API_KEY and self.LLM_PROVIDER == "huggingface":
                errors.append("HF_API_KEY required when LLM_PROVIDER=huggingface")
            if not self.OPENAI_API_KEY and self.LLM_PROVIDER == "openai":
                errors.append("OPENAI_API_KEY required when LLM_PROVIDER=openai")
        
        # Numeric ranges
        if self.LLM_TIMEOUT <= 0:
            errors.append(f"Invalid LLM_TIMEOUT: {self.LLM_TIMEOUT} (must be > 0)")
        if self.LLM_MAX_RETRIES < 0:
            errors.append(f"Invalid LLM_MAX_RETRIES: {self.LLM_MAX_RETRIES} (must be >= 0)")
        if not 0 <= self.LLM_DEFAULT_TEMPERATURE <= 2:
            errors.append(f"Invalid LLM_DEFAULT_TEMPERATURE: {self.LLM_DEFAULT_TEMPERATURE}")
        if self.MAX_QUERY_LENGTH <= 0:
            errors.append(f"Invalid MAX_QUERY_LENGTH: {self.MAX_QUERY_LENGTH}")
        
        # Fail fast on critical errors
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)
        
        # ==========================================================================
        # Non-fatal Warnings (development only)
        # ==========================================================================
        
        if not self.is_production():
            import warnings
            if self.USE_MOCK_EMBEDDINGS:
                warnings.warn("Mock embeddings enabled - not for production use")
            if self.USE_MOCK_LLM:
                warnings.warn("Mock LLM enabled - not for production use")
            if self.CORS_ORIGINS == ["*"]:
                warnings.warn("CORS allows all origins - restrict in production")
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    def get_llm_config(self) -> dict:
        """Get LLM configuration as a dictionary."""
        return {
            "provider": self.LLM_PROVIDER,
            "use_mock": self.USE_MOCK_LLM,
            "ollama_base_url": self.LLM_BASE_URL,
            "ollama_model": self.LLM_MODEL,
            "hf_model": self.HF_LLM_MODEL,
            "openai_model": self.OPENAI_MODEL,
            "timeout": self.LLM_TIMEOUT,
            "max_retries": self.LLM_MAX_RETRIES,
            "default_max_tokens": self.LLM_DEFAULT_MAX_TOKENS,
            "default_temperature": self.LLM_DEFAULT_TEMPERATURE
        }
    
    def get_config_summary(self) -> dict:
        """Get a summary of current configuration (safe for logging)."""
        # Determine active model based on provider
        if self.LLM_PROVIDER == "ollama":
            active_model = self.LLM_MODEL
        elif self.LLM_PROVIDER == "huggingface":
            active_model = self.HF_LLM_MODEL
        else:
            active_model = self.OPENAI_MODEL
        
        return {
            "environment": "production" if self.is_production() else "development",
            "api_port": self.API_PORT,
            "database": self.MONGODB_DATABASE,
            "llm_provider": self.LLM_PROVIDER,
            "llm_base_url": self.LLM_BASE_URL if self.LLM_PROVIDER == "ollama" else None,
            "use_mock_llm": self.USE_MOCK_LLM,
            "use_mock_embeddings": self.USE_MOCK_EMBEDDINGS,
            "embedding_model": self.HF_EMBEDDING_MODEL,
            "llm_model": active_model,
            "rate_limits": {
                "ingest": self.RATE_LIMIT_INGEST,
                "retrieve": self.RATE_LIMIT_RETRIEVE,
                "generate": self.RATE_LIMIT_GENERATE
            }
        }


# Global settings instance
settings = Settings()

