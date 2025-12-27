"""
MongoDB document models for DocuMind AI backend.
Defines Pydantic models for Job and CodeChunk documents.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Enum representing possible job statuses."""
    PENDING = "pending"
    CLONING = "cloning"
    SCANNING = "scanning"
    PARSING = "parsing"
    CHUNKING = "chunking"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobTimestamps(BaseModel):
    """Timestamps for each phase of the job."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    cloning_started_at: Optional[datetime] = None
    cloning_completed_at: Optional[datetime] = None
    scanning_started_at: Optional[datetime] = None
    scanning_completed_at: Optional[datetime] = None
    parsing_started_at: Optional[datetime] = None
    parsing_completed_at: Optional[datetime] = None
    chunking_started_at: Optional[datetime] = None
    chunking_completed_at: Optional[datetime] = None
    storing_started_at: Optional[datetime] = None
    storing_completed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None


class JobStats(BaseModel):
    """Statistics about the ingestion job."""
    total_files: int = 0
    processed_files: int = 0
    total_chunks: int = 0
    total_lines: int = 0
    files_by_language: Dict[str, int] = Field(default_factory=dict)


class Job(BaseModel):
    """
    MongoDB document model for an ingestion job.
    
    Attributes:
        job_id: Unique identifier for the job (UUID)
        repo_url: GitHub repository URL
        repo_owner: Repository owner
        repo_name: Repository name
        local_path: Local path where repo is cloned
        status: Current job status
        error_message: Error message if job failed
        timestamps: Timestamps for each phase
        stats: Job statistics
    """
    job_id: str = Field(..., description="Unique job identifier (UUID)")
    repo_url: str = Field(..., description="GitHub repository URL")
    repo_owner: str = Field(..., description="Repository owner/organization")
    repo_name: str = Field(..., description="Repository name")
    local_path: Optional[str] = Field(None, description="Local clone path")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    timestamps: JobTimestamps = Field(default_factory=JobTimestamps)
    stats: JobStats = Field(default_factory=JobStats)
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_mongo_dict(self) -> Dict[str, Any]:
        """Convert model to MongoDB-compatible dictionary."""
        data = self.model_dump()
        # Ensure _id is not set (let MongoDB generate it)
        data.pop('_id', None)
        return data
    
    @classmethod
    def from_mongo_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create model from MongoDB document.
        
        Handles legacy documents that may be missing repo_owner/repo_name fields
        by extracting them from repo_url.
        """
        # Remove MongoDB _id field
        data.pop('_id', None)
        
        # Handle legacy documents missing repo_owner/repo_name
        if 'repo_owner' not in data or 'repo_name' not in data:
            repo_url = data.get('repo_url', '')
            # Extract from URL: https://github.com/owner/repo or https://github.com/owner/repo.git
            try:
                # Remove .git suffix if present
                clean_url = repo_url.rstrip('/').removesuffix('.git')
                parts = clean_url.split('/')
                if len(parts) >= 2:
                    data.setdefault('repo_name', parts[-1])
                    data.setdefault('repo_owner', parts[-2])
                else:
                    # Fallback to unknown if can't parse
                    data.setdefault('repo_owner', 'unknown')
                    data.setdefault('repo_name', 'unknown')
            except Exception:
                data.setdefault('repo_owner', 'unknown')
                data.setdefault('repo_name', 'unknown')
        
        return cls(**data)


class CodeChunk(BaseModel):
    """
    MongoDB document model for a code chunk.
    
    Attributes:
        chunk_id: Unique identifier for the chunk
        job_id: Reference to parent job
        file_path: Relative path to source file
        language: Programming language
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed)
        content: Chunk content (code/text)
        token_count: Approximate token count
        metadata: Additional metadata
    """
    chunk_id: str = Field(..., description="Unique chunk identifier")
    job_id: str = Field(..., description="Parent job ID")
    file_path: str = Field(..., description="Relative file path")
    language: str = Field(..., description="Programming language")
    start_line: int = Field(..., ge=1, description="Start line (1-indexed)")
    end_line: int = Field(..., ge=1, description="End line (1-indexed)")
    content: str = Field(..., description="Chunk content")
    token_count: int = Field(default=0, ge=0, description="Approximate token count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_mongo_dict(self) -> Dict[str, Any]:
        """Convert model to MongoDB-compatible dictionary."""
        data = self.model_dump()
        data.pop('_id', None)
        return data
    
    @classmethod
    def from_mongo_dict(cls, data: Dict[str, Any]) -> 'CodeChunk':
        """Create model from MongoDB document."""
        data.pop('_id', None)
        return cls(**data)


# Request/Response models for API
class IngestRequest(BaseModel):
    """Request model for /ingest endpoint."""
    repo_url: str = Field(..., description="GitHub repository URL to ingest")


class IngestResponse(BaseModel):
    """Response model for /ingest endpoint."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")


class JobStatusResponse(BaseModel):
    """Response model for job status endpoint."""
    job_id: str
    status: str
    repo_url: str
    repo_name: str
    error_message: Optional[str] = None
    stats: JobStats
    timestamps: JobTimestamps


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    database: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Phase 2: Embedding Document Model
# =============================================================================

class EmbeddingRecord(BaseModel):
    """
    MongoDB document model for an embedding record.
    
    Attributes:
        job_id: Reference to parent job
        chunk_id: Reference to source chunk
        file_path: Relative path to source file
        content: Original chunk content
        embedding: Vector embedding
        language: Programming language
        start_line: Starting line number
        end_line: Ending line number
        metadata: Additional metadata
    """
    job_id: str = Field(..., description="Parent job ID")
    chunk_id: str = Field(..., description="Source chunk ID")
    file_path: str = Field(..., description="Relative file path")
    content: str = Field(..., description="Chunk content")
    embedding: List[float] = Field(..., description="Vector embedding")
    language: Optional[str] = Field(None, description="Programming language")
    start_line: Optional[int] = Field(None, description="Start line (1-indexed)")
    end_line: Optional[int] = Field(None, description="End line (1-indexed)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_mongo_dict(self) -> Dict[str, Any]:
        """Convert model to MongoDB-compatible dictionary."""
        data = self.model_dump()
        data.pop('_id', None)
        return data
    
    @classmethod
    def from_mongo_dict(cls, data: Dict[str, Any]) -> 'EmbeddingRecord':
        """Create model from MongoDB document."""
        data.pop('_id', None)
        return cls(**data)

