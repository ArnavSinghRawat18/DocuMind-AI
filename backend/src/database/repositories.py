"""
Database repository layer for DocuMind AI backend.
Provides CRUD operations for Job and CodeChunk documents.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pymongo.errors import DuplicateKeyError, BulkWriteError

from src.config import settings
from src.database.mongodb import get_jobs_collection, get_chunks_collection
from src.database.models import Job, CodeChunk, JobStatus, JobStats
from src.utils.logger import get_database_logger

logger = get_database_logger()


class JobRepository:
    """Repository for Job document operations."""
    
    @staticmethod
    def create_job(job: Job) -> str:
        """
        Insert a new job into the database.
        
        Args:
            job: Job model instance
            
        Returns:
            job_id of the created job
            
        Raises:
            DuplicateKeyError: If job_id already exists
        """
        collection = get_jobs_collection()
        job_dict = job.to_mongo_dict()
        
        try:
            collection.insert_one(job_dict)
            logger.info(f"Created job: {job.job_id}")
            return job.job_id
        except DuplicateKeyError:
            logger.error(f"Job already exists: {job.job_id}")
            raise
    
    @staticmethod
    def get_job(job_id: str) -> Optional[Job]:
        """
        Retrieve a job by its ID.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Job instance or None if not found
        """
        collection = get_jobs_collection()
        job_dict = collection.find_one({"job_id": job_id})
        
        if job_dict:
            return Job.from_mongo_dict(job_dict)
        return None
    
    @staticmethod
    def update_job_status(
        job_id: str, 
        status: JobStatus, 
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update job status and corresponding timestamp.
        
        Args:
            job_id: Unique job identifier
            status: New job status
            error_message: Optional error message (for failed status)
            
        Returns:
            True if job was updated, False if not found
        """
        collection = get_jobs_collection()
        
        # Build update document
        update_doc: Dict[str, Any] = {
            "$set": {
                "status": status.value
            }
        }
        
        # Set appropriate timestamp based on status
        timestamp_field = JobRepository._get_timestamp_field(status)
        if timestamp_field:
            update_doc["$set"][f"timestamps.{timestamp_field}"] = datetime.utcnow()
        
        # Add error message if provided
        if error_message:
            update_doc["$set"]["error_message"] = error_message
        
        result = collection.update_one(
            {"job_id": job_id},
            update_doc
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated job {job_id} status to {status.value}")
            return True
        
        logger.warning(f"Job not found for status update: {job_id}")
        return False
    
    @staticmethod
    def _get_timestamp_field(status: JobStatus) -> Optional[str]:
        """Map job status to corresponding timestamp field."""
        status_to_timestamp = {
            JobStatus.PENDING: "created_at",
            JobStatus.CLONING: "cloning_started_at",
            JobStatus.SCANNING: "scanning_started_at",
            JobStatus.PARSING: "parsing_started_at",
            JobStatus.CHUNKING: "chunking_started_at",
            JobStatus.STORING: "storing_started_at",
            JobStatus.COMPLETED: "completed_at",
            JobStatus.FAILED: "failed_at",
        }
        return status_to_timestamp.get(status)
    
    @staticmethod
    def update_job_stats(job_id: str, stats: JobStats) -> bool:
        """
        Update job statistics.
        
        Args:
            job_id: Unique job identifier
            stats: Updated job statistics
            
        Returns:
            True if job was updated, False if not found
        """
        collection = get_jobs_collection()
        
        result = collection.update_one(
            {"job_id": job_id},
            {"$set": {"stats": stats.model_dump()}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated stats for job {job_id}")
            return True
        return False
    
    @staticmethod
    def update_job_local_path(job_id: str, local_path: str) -> bool:
        """
        Update job's local repository path.
        
        Args:
            job_id: Unique job identifier
            local_path: Local path where repo is cloned
            
        Returns:
            True if job was updated, False if not found
        """
        collection = get_jobs_collection()
        
        result = collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "local_path": local_path,
                    "timestamps.cloning_completed_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def set_phase_complete(job_id: str, phase: str) -> bool:
        """
        Mark a phase as complete with timestamp.
        
        Args:
            job_id: Unique job identifier
            phase: Phase name (cloning, scanning, parsing, chunking, storing)
            
        Returns:
            True if updated successfully
        """
        collection = get_jobs_collection()
        
        result = collection.update_one(
            {"job_id": job_id},
            {"$set": {f"timestamps.{phase}_completed_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def list_jobs(
        status: Optional[JobStatus] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Job]:
        """
        List jobs with optional status filter.
        
        Args:
            status: Optional status filter
            limit: Maximum number of jobs to return
            skip: Number of jobs to skip (for pagination)
            
        Returns:
            List of Job instances
        """
        collection = get_jobs_collection()
        
        query = {}
        if status:
            query["status"] = status.value
        
        cursor = collection.find(query).sort(
            "timestamps.created_at", -1
        ).skip(skip).limit(limit)
        
        return [Job.from_mongo_dict(doc) for doc in cursor]
    
    @staticmethod
    def delete_job(job_id: str) -> bool:
        """
        Delete a job by its ID.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            True if job was deleted, False if not found
        """
        collection = get_jobs_collection()
        result = collection.delete_one({"job_id": job_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted job: {job_id}")
            return True
        return False


class ChunkRepository:
    """Repository for CodeChunk document operations."""
    
    @staticmethod
    def insert_chunks_bulk(chunks: List[CodeChunk]) -> int:
        """
        Insert multiple chunks in bulk.
        
        Args:
            chunks: List of CodeChunk instances
            
        Returns:
            Number of chunks inserted
        """
        if not chunks:
            return 0
        
        collection = get_chunks_collection()
        chunk_dicts = [chunk.to_mongo_dict() for chunk in chunks]
        
        try:
            result = collection.insert_many(chunk_dicts, ordered=False)
            inserted_count = len(result.inserted_ids)
            logger.info(f"Bulk inserted {inserted_count} chunks")
            return inserted_count
        except BulkWriteError as e:
            # Some documents may have been inserted
            inserted_count = e.details.get('nInserted', 0)
            logger.warning(f"Bulk insert partial success: {inserted_count} chunks inserted")
            return inserted_count
    
    @staticmethod
    def get_chunks_by_job(job_id: str, limit: int = 1000) -> List[CodeChunk]:
        """
        Retrieve all chunks for a specific job.
        
        Args:
            job_id: Unique job identifier
            limit: Maximum number of chunks to return
            
        Returns:
            List of CodeChunk instances
        """
        collection = get_chunks_collection()
        
        cursor = collection.find(
            {"job_id": job_id}
        ).sort([
            ("file_path", 1),
            ("start_line", 1)
        ]).limit(limit)
        
        return [CodeChunk.from_mongo_dict(doc) for doc in cursor]
    
    @staticmethod
    def get_chunk(chunk_id: str) -> Optional[CodeChunk]:
        """
        Retrieve a specific chunk by ID.
        
        Args:
            chunk_id: Unique chunk identifier
            
        Returns:
            CodeChunk instance or None if not found
        """
        collection = get_chunks_collection()
        chunk_dict = collection.find_one({"chunk_id": chunk_id})
        
        if chunk_dict:
            return CodeChunk.from_mongo_dict(chunk_dict)
        return None
    
    @staticmethod
    def count_chunks_by_job(job_id: str) -> int:
        """
        Count total chunks for a job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Number of chunks
        """
        collection = get_chunks_collection()
        return collection.count_documents({"job_id": job_id})
    
    @staticmethod
    def get_chunks_by_file(job_id: str, file_path: str) -> List[CodeChunk]:
        """
        Retrieve all chunks for a specific file within a job.
        
        Args:
            job_id: Unique job identifier
            file_path: Relative file path
            
        Returns:
            List of CodeChunk instances sorted by line number
        """
        collection = get_chunks_collection()
        
        cursor = collection.find({
            "job_id": job_id,
            "file_path": file_path
        }).sort("start_line", 1)
        
        return [CodeChunk.from_mongo_dict(doc) for doc in cursor]
    
    @staticmethod
    def delete_chunks_by_job(job_id: str) -> int:
        """
        Delete all chunks for a job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Number of chunks deleted
        """
        collection = get_chunks_collection()
        result = collection.delete_many({"job_id": job_id})
        
        logger.info(f"Deleted {result.deleted_count} chunks for job {job_id}")
        return result.deleted_count
