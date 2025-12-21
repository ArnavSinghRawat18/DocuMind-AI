"""
Ingestion API routes for DocuMind AI.
Handles repository ingestion pipeline orchestration.
"""

import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, status

from src.config import settings
from src.database.models import (
    Job, JobStatus, JobStats, JobTimestamps,
    IngestRequest, IngestResponse, JobStatusResponse,
    CodeChunk
)
from src.database.repositories import JobRepository, ChunkRepository
from src.ingestion.git_client import GitClient, GitClientError
from src.ingestion.file_walker import FileWalker, get_language_from_extension
from src.ingestion.parser import FileParser, FileParseError
from src.ingestion.chunker import TextChunker
from src.utils.validators import validate_github_url, extract_repo_info
from src.utils.logger import get_api_logger

logger = get_api_logger()

# Create router
router = APIRouter(prefix="/api/v1", tags=["ingestion"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a GitHub repository",
    description="Start ingestion of a public GitHub repository. Returns job ID immediately."
)
async def ingest_repository(
    request: IngestRequest,
    background_tasks: BackgroundTasks
) -> IngestResponse:
    """
    Start the ingestion pipeline for a GitHub repository.
    
    This endpoint:
    1. Validates the repository URL
    2. Creates a job record
    3. Triggers the ingestion pipeline in the background
    4. Returns the job ID immediately
    
    Args:
        request: IngestRequest with repo_url
        background_tasks: FastAPI background tasks handler
        
    Returns:
        IngestResponse with job_id and status
    """
    # Validate GitHub URL
    is_valid, error_msg = validate_github_url(request.repo_url)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Extract repository information
    try:
        repo_owner, repo_name = extract_repo_info(request.repo_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job record
    job = Job(
        job_id=job_id,
        repo_url=request.repo_url,
        repo_owner=repo_owner,
        repo_name=repo_name,
        status=JobStatus.PENDING,
        timestamps=JobTimestamps(created_at=datetime.utcnow()),
        stats=JobStats()
    )
    
    try:
        JobRepository.create_job(job)
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ingestion job"
        )
    
    # Start ingestion in background
    background_tasks.add_task(run_ingestion_pipeline, job_id, request.repo_url)
    
    logger.info(f"Created ingestion job: {job_id} for {request.repo_url}")
    
    return IngestResponse(
        job_id=job_id,
        status=JobStatus.PENDING.value,
        message=f"Ingestion started for {repo_owner}/{repo_name}"
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Get the current status and details of an ingestion job."
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get the current status of an ingestion job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        JobStatusResponse with current status and statistics
    """
    job = JobRepository.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        repo_url=job.repo_url,
        repo_name=job.repo_name,
        error_message=job.error_message,
        stats=job.stats,
        timestamps=job.timestamps
    )


@router.get(
    "/jobs",
    summary="List jobs",
    description="List all ingestion jobs with optional status filter."
)
async def list_jobs(
    status_filter: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
):
    """
    List all ingestion jobs.
    
    Args:
        status_filter: Optional status filter (pending, completed, failed, etc.)
        limit: Maximum number of jobs to return
        skip: Number of jobs to skip (pagination)
        
    Returns:
        List of jobs
    """
    # Validate status filter
    filter_status = None
    if status_filter:
        try:
            filter_status = JobStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Valid values: {[s.value for s in JobStatus]}"
            )
    
    jobs = JobRepository.list_jobs(status=filter_status, limit=limit, skip=skip)
    
    return {
        "jobs": [
            {
                "job_id": job.job_id,
                "repo_url": job.repo_url,
                "repo_name": job.repo_name,
                "status": job.status,
                "created_at": job.timestamps.created_at,
                "stats": job.stats.model_dump()
            }
            for job in jobs
        ],
        "total": len(jobs),
        "limit": limit,
        "skip": skip
    }


@router.get(
    "/jobs/{job_id}/chunks",
    summary="Get job chunks",
    description="Get all code chunks for a completed job."
)
async def get_job_chunks(
    job_id: str,
    limit: int = 100,
    file_path: Optional[str] = None
):
    """
    Get code chunks for a job.
    
    Args:
        job_id: Unique job identifier
        limit: Maximum chunks to return
        file_path: Optional filter by file path
        
    Returns:
        List of code chunks
    """
    # Verify job exists
    job = JobRepository.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    # Get chunks
    if file_path:
        chunks = ChunkRepository.get_chunks_by_file(job_id, file_path)
    else:
        chunks = ChunkRepository.get_chunks_by_job(job_id, limit=limit)
    
    return {
        "job_id": job_id,
        "chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "file_path": chunk.file_path,
                "language": chunk.language,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "token_count": chunk.token_count,
                "content": chunk.content
            }
            for chunk in chunks
        ],
        "total": len(chunks)
    }


# =============================================================================
# Ingestion Pipeline
# =============================================================================

async def run_ingestion_pipeline(job_id: str, repo_url: str) -> None:
    """
    Run the complete ingestion pipeline.
    
    Pipeline stages:
    1. Clone repository
    2. Scan for files
    3. Parse files
    4. Chunk content
    5. Store in MongoDB
    
    Args:
        job_id: Unique job identifier
        repo_url: GitHub repository URL
    """
    logger.info(f"Starting ingestion pipeline for job: {job_id}")
    
    git_client = GitClient()
    file_walker = FileWalker()
    file_parser = FileParser()
    chunker = TextChunker()
    
    local_path = None
    stats = JobStats()
    
    try:
        # =================================================================
        # Stage 1: Clone Repository
        # =================================================================
        JobRepository.update_job_status(job_id, JobStatus.CLONING)
        logger.info(f"[{job_id}] Cloning repository: {repo_url}")
        
        try:
            local_path, repo_name = git_client.clone_repository(repo_url, job_id)
            JobRepository.update_job_local_path(job_id, local_path)
            logger.info(f"[{job_id}] Clone complete: {local_path}")
        except GitClientError as e:
            raise IngestionError(f"Failed to clone repository: {e}")
        
        # =================================================================
        # Stage 2: Scan Files
        # =================================================================
        JobRepository.update_job_status(job_id, JobStatus.SCANNING)
        logger.info(f"[{job_id}] Scanning files...")
        
        files = file_walker.get_all_files(local_path)
        stats.total_files = len(files)
        
        if not files:
            logger.warning(f"[{job_id}] No matching files found in repository")
            raise IngestionError(
                "No supported files found in repository. "
                f"Supported extensions: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Count files by language
        for file_info in files:
            lang = get_language_from_extension(file_info.extension)
            stats.files_by_language[lang] = stats.files_by_language.get(lang, 0) + 1
        
        logger.info(f"[{job_id}] Found {stats.total_files} files")
        JobRepository.set_phase_complete(job_id, "scanning")
        
        # =================================================================
        # Stage 3 & 4: Parse and Chunk Files
        # =================================================================
        JobRepository.update_job_status(job_id, JobStatus.PARSING)
        logger.info(f"[{job_id}] Parsing files...")
        
        all_chunks = []
        
        for file_info in files:
            try:
                # Parse file
                parsed_file = file_parser.parse_file(file_info)
                stats.total_lines += parsed_file.total_lines
                stats.processed_files += 1
                
                # Chunk file
                file_chunks = chunker.chunk_file(parsed_file, job_id)
                all_chunks.extend(file_chunks)
                
            except FileParseError as e:
                logger.warning(f"[{job_id}] Failed to parse {file_info.relative_path}: {e}")
                continue
            except Exception as e:
                logger.warning(f"[{job_id}] Error processing {file_info.relative_path}: {e}")
                continue
        
        JobRepository.set_phase_complete(job_id, "parsing")
        
        # Update to chunking status
        JobRepository.update_job_status(job_id, JobStatus.CHUNKING)
        stats.total_chunks = len(all_chunks)
        logger.info(f"[{job_id}] Generated {stats.total_chunks} chunks from {stats.processed_files} files")
        JobRepository.set_phase_complete(job_id, "chunking")
        
        # =================================================================
        # Stage 5: Store Chunks
        # =================================================================
        JobRepository.update_job_status(job_id, JobStatus.STORING)
        logger.info(f"[{job_id}] Storing chunks in database...")
        
        if all_chunks:
            # Convert Chunk objects to CodeChunk models
            code_chunks = [
                CodeChunk(
                    chunk_id=chunk.chunk_id,
                    job_id=chunk.job_id,
                    file_path=chunk.file_path,
                    language=chunk.language,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    metadata={"line_count": chunk.end_line - chunk.start_line + 1}
                )
                for chunk in all_chunks
            ]
            
            # Bulk insert chunks
            inserted_count = ChunkRepository.insert_chunks_bulk(code_chunks)
            logger.info(f"[{job_id}] Stored {inserted_count} chunks")
        
        JobRepository.set_phase_complete(job_id, "storing")
        
        # =================================================================
        # Complete
        # =================================================================
        JobRepository.update_job_stats(job_id, stats)
        JobRepository.update_job_status(job_id, JobStatus.COMPLETED)
        
        logger.info(
            f"[{job_id}] Ingestion complete: "
            f"{stats.processed_files} files, {stats.total_chunks} chunks"
        )
        
    except IngestionError as e:
        logger.error(f"[{job_id}] Ingestion failed: {e}")
        JobRepository.update_job_stats(job_id, stats)
        JobRepository.update_job_status(job_id, JobStatus.FAILED, str(e))
        
    except Exception as e:
        logger.exception(f"[{job_id}] Unexpected error during ingestion: {e}")
        JobRepository.update_job_stats(job_id, stats)
        JobRepository.update_job_status(
            job_id, 
            JobStatus.FAILED, 
            f"Unexpected error: {str(e)}"
        )


class IngestionError(Exception):
    """Custom exception for ingestion pipeline errors."""
    pass
