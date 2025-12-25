"""
Retrieval API routes for DocuMind AI.
Handles semantic search and chunk retrieval for RAG.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field

from src.config import settings
from src.retrieval.retriever import Retriever, RetrieverError, RetrievalResult
from src.database.repositories import JobRepository
from src.utils.logger import get_api_logger
from src.utils.validators import validate_query, sanitize_query
from src.api.middleware import limiter

logger = get_api_logger()

# Create router
router = APIRouter(prefix="/api/v1", tags=["retrieval"])


# =============================================================================
# Request/Response Models
# =============================================================================

class RetrieveRequest(BaseModel):
    """Request model for /retrieve endpoint."""
    job_id: str = Field(..., description="Job ID to search within")
    query: str = Field(..., description="Search query string", min_length=1)
    top_k: int = Field(
        default=5, 
        ge=1, 
        le=50, 
        description="Number of results to return"
    )
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0-1)"
    )


class ChunkMatch(BaseModel):
    """A single matched chunk in retrieval results."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    file_path: str = Field(..., description="File path within repository")
    content: str = Field(..., description="Chunk content")
    score: float = Field(..., description="Similarity score (0-1)")
    language: Optional[str] = Field(None, description="Programming language")
    start_line: Optional[int] = Field(None, description="Starting line number")
    end_line: Optional[int] = Field(None, description="Ending line number")


class RetrieveResponse(BaseModel):
    """Response model for /retrieve endpoint."""
    job_id: str = Field(..., description="Job ID searched")
    query: str = Field(..., description="Original query")
    matches: List[ChunkMatch] = Field(..., description="Matched chunks")
    total_matches: int = Field(..., description="Number of matches returned")


class EmbedRequest(BaseModel):
    """Request model for /embed endpoint."""
    job_id: str = Field(..., description="Job ID to embed chunks for")


class EmbedResponse(BaseModel):
    """Response model for /embed endpoint."""
    job_id: str = Field(..., description="Job ID")
    chunks_embedded: int = Field(..., description="Number of chunks embedded")
    message: str = Field(..., description="Status message")


class EmbeddingStatsResponse(BaseModel):
    """Response model for embedding stats endpoint."""
    job_id: str
    total_chunks: int
    embedded_chunks: int
    embedding_coverage: float
    is_complete: bool


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/retrieve",
    response_model=RetrieveResponse,
    summary="Retrieve relevant code chunks",
    description="Perform semantic search to find code chunks relevant to a query."
)
@limiter.limit("60/minute")
async def retrieve_chunks(request: Request, body: RetrieveRequest) -> RetrieveResponse:
    """
    Retrieve the most relevant code chunks for a query using vector similarity.
    
    This endpoint:
    1. Generates an embedding for the query
    2. Performs vector similarity search against job's embedded chunks
    3. Returns ranked results with relevance scores
    
    If chunks are not yet embedded, embedding is performed automatically.
    
    Args:
        request: Starlette Request (for rate limiting)
        body: RetrieveRequest with job_id, query, and optional parameters
        
    Returns:
        RetrieveResponse with matched chunks
    """
    # Validate query
    is_valid, error_msg = validate_query(body.query)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    sanitized_query = sanitize_query(body.query)
    logger.info(f"Retrieve request for job {body.job_id}: '{sanitized_query[:50]}...'")
    
    # Validate job exists
    job = JobRepository.get_job(body.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {body.job_id}"
        )
    
    # Check job is completed
    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job.status}"
        )
    
    # Perform retrieval
    try:
        retriever = Retriever()
        results = await retriever.retrieve(
            query=body.query,
            job_id=body.job_id,
            top_k=body.top_k,
            score_threshold=body.score_threshold
        )
    except RetrieverError as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    # Convert to response model
    matches = [
        ChunkMatch(
            chunk_id=r.chunk_id,
            file_path=r.file_path,
            content=r.content,
            score=round(r.score, 4),
            language=r.language,
            start_line=r.start_line,
            end_line=r.end_line
        )
        for r in results
    ]
    
    logger.info(f"Returning {len(matches)} matches for job {body.job_id}")
    
    return RetrieveResponse(
        job_id=body.job_id,
        query=body.query,
        matches=matches,
        total_matches=len(matches)
    )


@router.post(
    "/embed/{job_id}",
    response_model=EmbedResponse,
    summary="Embed job chunks",
    description="Generate and store embeddings for all chunks of a job."
)
async def embed_job(job_id: str) -> EmbedResponse:
    """
    Generate embeddings for all chunks of a completed job.
    
    This endpoint is optional - retrieval will automatically embed chunks
    if not already done. Use this to pre-compute embeddings.
    
    Args:
        job_id: Job ID to embed chunks for
        
    Returns:
        EmbedResponse with embedding count
    """
    logger.info(f"Embed request for job {job_id}")
    
    # Validate job exists
    job = JobRepository.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    # Check job is completed
    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job.status}"
        )
    
    # Generate embeddings
    try:
        retriever = Retriever()
        count = await retriever.embed_job_chunks(job_id)
    except RetrieverError as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return EmbedResponse(
        job_id=job_id,
        chunks_embedded=count,
        message=f"Successfully embedded {count} chunks"
    )


@router.get(
    "/embed/{job_id}/stats",
    response_model=EmbeddingStatsResponse,
    summary="Get embedding stats",
    description="Get embedding statistics for a job."
)
async def get_embedding_stats(job_id: str) -> EmbeddingStatsResponse:
    """
    Get embedding statistics for a job.
    
    Args:
        job_id: Job ID to check
        
    Returns:
        EmbeddingStatsResponse with stats
    """
    # Validate job exists
    job = JobRepository.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    retriever = Retriever()
    stats = await retriever.get_embedding_stats(job_id)
    
    return EmbeddingStatsResponse(**stats)


@router.get(
    "/search/{job_id}",
    response_model=RetrieveResponse,
    summary="Search code chunks (GET)",
    description="Alternative GET endpoint for semantic search."
)
async def search_chunks(
    job_id: str,
    q: str,
    top_k: int = 5,
    threshold: Optional[float] = None
) -> RetrieveResponse:
    """
    Search code chunks using GET request.
    
    Convenience endpoint for simple searches without POST body.
    
    Args:
        job_id: Job ID to search within
        q: Search query string
        top_k: Number of results (default 5)
        threshold: Optional minimum score threshold
        
    Returns:
        RetrieveResponse with matched chunks
    """
    request = RetrieveRequest(
        job_id=job_id,
        query=q,
        top_k=top_k,
        score_threshold=threshold
    )
    return await retrieve_chunks(request)
