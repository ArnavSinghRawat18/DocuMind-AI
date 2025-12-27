"""
Generation API routes for DocuMind AI.
Handles RAG-based code documentation generation.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field, validator

from src.generation import (
    get_generator,
    GeneratorError,
    GenerationResponse,
    GenerationStatus
)
from src.database.repositories import JobRepository
from src.utils.logger import get_logger
from src.utils.validators import validate_query, sanitize_query
from src.api.middleware import limiter

logger = get_logger("documind.api.generation")

router = APIRouter(prefix="/api/v1/generate", tags=["Generation"])


# =============================================================================
# Request/Response Models
# =============================================================================

class GenerateRequest(BaseModel):
    """Request model for generation endpoint."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The question to answer about the codebase"
    )
    job_id: str = Field(
        ...,
        min_length=1,
        description="Job ID to search within"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of code chunks to retrieve for context"
    )
    max_tokens: int = Field(
        default=1024,
        ge=50,
        le=4096,
        description="Maximum tokens in the generated response"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM sampling temperature (0=deterministic, higher=creative)"
    )
    
    @validator("query")
    def validate_query(cls, v):
        """Validate and sanitize query."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()
    
    @validator("job_id")
    def validate_job_id(cls, v):
        """Validate job_id format."""
        if not v or not v.strip():
            raise ValueError("Job ID cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "query": "How does the authentication system work?",
                "job_id": "5fa93024-e32b-47f4-a7f1-8cfcce61b182",
                "top_k": 5,
                "max_tokens": 1024,
                "temperature": 0.7
            }
        }


class SourceModel(BaseModel):
    """Model for source references in response."""
    file_path: str
    start_line: int
    end_line: int
    language: str
    relevance_score: float
    snippet_preview: str


class GenerateResponseModel(BaseModel):
    """Response model for generation endpoint."""
    answer: str
    status: str
    sources: List[SourceModel]
    confidence: float
    model: str
    job_id: str
    query: str
    tokens_used: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The authentication system uses JWT tokens...",
                "status": "success",
                "sources": [
                    {
                        "file_path": "src/auth/jwt.py",
                        "start_line": 10,
                        "end_line": 45,
                        "language": "python",
                        "relevance_score": 0.85,
                        "snippet_preview": "def verify_token(token: str)..."
                    }
                ],
                "confidence": 0.85,
                "model": "mock-llm",
                "job_id": "5fa93024-e32b-47f4-a7f1-8cfcce61b182",
                "query": "How does authentication work?",
                "tokens_used": 256
            }
        }


class GenerateWithContextRequest(BaseModel):
    """Request model for generation with manual context."""
    query: str = Field(..., min_length=1, max_length=2000)
    context: List[Dict[str, Any]] = Field(
        ...,
        description="List of context chunks with file_path, content, language, etc."
    )
    max_tokens: int = Field(default=1024, ge=50, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What does this function do?",
                "context": [
                    {
                        "file_path": "src/utils.py",
                        "content": "def helper(): pass",
                        "language": "python",
                        "start_line": 1,
                        "end_line": 1
                    }
                ],
                "max_tokens": 512,
                "temperature": 0.5
            }
        }


class GenerateDocRequest(BaseModel):
    """Request model for documentation generation endpoint."""
    job_id: str = Field(
        ...,
        min_length=1,
        description="Job ID to generate documentation for"
    )
    doc_type: str = Field(
        default="README",
        description="Type of documentation to generate: README, API, ARCHITECTURE, DETAILED"
    )
    max_tokens: int = Field(
        default=12000,  # Ultra-high default for DETAILED enterprise docs
        ge=128,
        le=32768,
        description="Maximum tokens in the generated documentation (use 12000+ for DETAILED)"
    )
    temperature: float = Field(
        default=0.25,  # Low temp for consistent output
        ge=0.0,
        le=1.0,
        description="LLM temperature (lower = more consistent)"
    )
    
    @validator("job_id")
    def validate_job_id(cls, v):
        """Validate job_id format."""
        if not v or not v.strip():
            raise ValueError("Job ID cannot be empty")
        return v.strip()
    
    @validator("doc_type")
    def validate_doc_type(cls, v):
        """Validate doc_type."""
        valid_types = ["README", "API", "ARCHITECTURE", "DETAILED"]
        v_upper = v.upper() if v else "README"
        if v_upper not in valid_types:
            raise ValueError(f"Invalid doc_type. Must be one of: {valid_types}")
        return v_upper

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "dd4106f6-7e32-49b7-a37f-32e3b9f24071",
                "doc_type": "README",
                "max_tokens": 2048,
                "temperature": 0.5
            }
        }


class GenerateDocResponse(BaseModel):
    """Response model for documentation generation."""
    status: str
    content: str
    doc_type: str
    job_id: str
    model: str
    sources_count: int
    tokens_used: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "content": "# Project Name\\n\\n## Overview\\n...",
                "doc_type": "README",
                "job_id": "dd4106f6-7e32-49b7-a37f-32e3b9f24071",
                "model": "qwen3:8b",
                "sources_count": 10,
                "tokens_used": 1024
            }
        }


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "",
    response_model=GenerateResponseModel,
    summary="Generate documentation answer",
    description="""
    Generate an answer to a question about a codebase using RAG.
    
    This endpoint:
    1. Validates the job exists and has embeddings
    2. Retrieves relevant code chunks based on the query
    3. Builds a context-aware prompt
    4. Generates an answer using the configured LLM
    5. Returns the answer with source references
    
    **Response Status Values:**
    - `success`: Full answer with good context
    - `partial`: Answer generated with limited context  
    - `no_context`: No relevant code found
    - `error`: Generation failed
    """
)
@limiter.limit("30/minute")
async def generate(request: Request, body: GenerateRequest) -> GenerateResponseModel:
    """Generate an answer for a query about a codebase."""
    # Validate query
    is_valid, error_msg = validate_query(body.query)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=error_msg
        )
    
    sanitized_query = sanitize_query(body.query)
    logger.info(f"Generation request for job {body.job_id}: {sanitized_query[:50]}...")
    
    # Validate job exists
    job = JobRepository.get_job(body.job_id)
    if not job:
        logger.warning(f"Job not found: {body.job_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {body.job_id}"
        )
    
    # Check job status
    if job.status not in ["completed", "embedded"]:
        logger.warning(f"Job {body.job_id} not ready for generation: {job.status}")
        raise HTTPException(
            status_code=400,
            detail=f"Job not ready for generation. Current status: {job.status}. "
                   f"Job must be 'completed' or 'embedded'."
        )
    
    # Generate response
    try:
        generator = get_generator()
        response = await generator.generate(
            query=body.query,
            job_id=body.job_id,
            top_k=body.top_k,
            max_tokens=body.max_tokens,
            temperature=body.temperature
        )
        
        logger.info(
            f"Generation complete for job {body.job_id}: "
            f"status={response.status}, sources={len(response.sources)}"
        )
        
        return GenerateResponseModel(
            answer=response.answer,
            status=response.status.value,
            sources=[
                SourceModel(
                    file_path=s.file_path,
                    start_line=s.start_line,
                    end_line=s.end_line,
                    language=s.language,
                    relevance_score=s.relevance_score,
                    snippet_preview=s.snippet_preview
                )
                for s in response.sources
            ],
            confidence=response.confidence,
            model=response.model,
            job_id=response.job_id,
            query=response.query,
            tokens_used=response.tokens_used,
            error_message=response.error_message
        )
        
    except GeneratorError as e:
        logger.error(f"Generator error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error during generation: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during generation"
        )


@router.post(
    "/with-context",
    response_model=GenerateResponseModel,
    summary="Generate with manual context",
    description="Generate an answer using manually provided code context (for testing)"
)
async def generate_with_context(
    request: GenerateWithContextRequest
) -> GenerateResponseModel:
    """Generate an answer with manually provided context."""
    logger.info(f"Generation with manual context: {request.query[:50]}...")
    
    try:
        generator = get_generator()
        response = await generator.generate_with_context(
            query=request.query,
            context_chunks=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return GenerateResponseModel(
            answer=response.answer,
            status=response.status.value,
            sources=[
                SourceModel(
                    file_path=s.file_path,
                    start_line=s.start_line,
                    end_line=s.end_line,
                    language=s.language,
                    relevance_score=s.relevance_score,
                    snippet_preview=s.snippet_preview
                )
                for s in response.sources
            ],
            confidence=response.confidence,
            model=response.model,
            job_id=response.job_id,
            query=response.query,
            tokens_used=response.tokens_used,
            error_message=response.error_message
        )
        
    except Exception as e:
        logger.exception(f"Error during context generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )


@router.get(
    "/health",
    summary="Check generation service health",
    description="Verify the generation service is operational"
)
async def generation_health() -> Dict[str, Any]:
    """Check the health of the generation service."""
    try:
        generator = get_generator()
        return {
            "status": "healthy",
            "model": generator._llm_client.get_model_name(),
            "provider": type(generator._llm_client).__name__
        }
    except Exception as e:
        logger.error(f"Generation health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post(
    "/docs",
    response_model=GenerateDocResponse,
    summary="Generate documentation for a codebase",
    description="""
    Generate structured documentation (README, API docs, Architecture) for an ingested codebase.
    
    **Supported doc_type values:**
    - `README`: Comprehensive README.md with overview, tech stack, setup, etc.
    - `API`: API documentation with endpoints and examples
    - `ARCHITECTURE`: System architecture and design documentation
    
    **Requirements:**
    - Job must be in 'completed' status
    - Uses Ollama with qwen3:8b model by default
    """
)
@limiter.limit("10/minute")
async def generate_documentation(
    request: Request,
    body: GenerateDocRequest
) -> GenerateDocResponse:
    """Generate documentation for a codebase."""
    logger.info(f"Documentation generation request: {body.doc_type} for job {body.job_id}")
    
    # Validate job exists
    job = JobRepository.get_job(body.job_id)
    if not job:
        logger.warning(f"Job not found: {body.job_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {body.job_id}"
        )
    
    # Check job status
    if job.status not in ["completed", "embedded"]:
        logger.warning(f"Job {body.job_id} not ready: {job.status}")
        raise HTTPException(
            status_code=400,
            detail=f"Job not ready for documentation generation. Current status: {job.status}. "
                   f"Job must be 'completed' or 'embedded'."
        )
    
    # Generate documentation
    try:
        generator = get_generator()
        response = await generator.generate_documentation(
            job_id=body.job_id,
            doc_type=body.doc_type,
            repo_name=getattr(job, 'repo_name', ''),
            repo_owner=getattr(job, 'repo_owner', ''),
            max_tokens=body.max_tokens,
            temperature=body.temperature
        )
        
        logger.info(
            f"Documentation generation complete for job {body.job_id}: "
            f"type={body.doc_type}, sources={len(response.sources)}, "
            f"tokens={response.tokens_used}"
        )
        
        return GenerateDocResponse(
            status=response.status.value,
            content=response.answer,
            doc_type=body.doc_type,
            job_id=body.job_id,
            model=response.model,
            sources_count=len(response.sources),
            tokens_used=response.tokens_used,
            error_message=response.error_message
        )
        
    except GeneratorError as e:
        logger.error(f"Generator error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Documentation generation failed: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error during documentation generation: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during documentation generation"
        )

