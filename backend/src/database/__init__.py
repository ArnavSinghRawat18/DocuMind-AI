"""
Database module for DocuMind AI.
Handles MongoDB connections, models, and repository operations.
"""

from src.database.mongodb import db, get_db, get_jobs_collection, get_chunks_collection
from src.database.models import (
    Job, JobStatus, JobTimestamps, JobStats,
    CodeChunk, IngestRequest, IngestResponse,
    JobStatusResponse, HealthResponse
)
from src.database.repositories import JobRepository, ChunkRepository

__all__ = [
    # MongoDB
    "db",
    "get_db",
    "get_jobs_collection",
    "get_chunks_collection",
    # Models
    "Job",
    "JobStatus",
    "JobTimestamps",
    "JobStats",
    "CodeChunk",
    "IngestRequest",
    "IngestResponse",
    "JobStatusResponse",
    "HealthResponse",
    # Repositories
    "JobRepository",
    "ChunkRepository",
]
