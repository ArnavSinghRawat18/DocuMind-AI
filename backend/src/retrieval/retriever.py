"""
Retriever module for DocuMind AI.
Combines embedding generation and vector search for RAG retrieval.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from src.config import settings
from src.embeddings.embedding_service import EmbeddingService, get_embedding_service
from src.embeddings.vector_store import VectorStore, get_vector_store, SearchResult
from src.database.repositories import JobRepository, ChunkRepository
from src.database.models import CodeChunk
from src.utils.logger import get_logger

logger = get_logger("documind.retriever")


@dataclass
class RetrievalResult:
    """Represents a retrieval result with chunk content and metadata."""
    chunk_id: str
    file_path: str
    content: str
    score: float
    language: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class RetrieverError(Exception):
    """Custom exception for retriever operations."""
    pass


class Retriever:
    """
    Retriever for semantic code search.
    
    Combines embedding generation and vector similarity search
    to find the most relevant code chunks for a given query.
    """
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None
    ):
        """
        Initialize the retriever.
        
        Args:
            embedding_service: Embedding service instance
            vector_store: Vector store instance
        """
        self._embedding_service = embedding_service or get_embedding_service()
        self._vector_store = vector_store or get_vector_store()
        
        logger.info("Initialized Retriever")
    
    async def retrieve(
        self,
        query: str,
        job_id: str,
        top_k: int = None,
        score_threshold: float = None
    ) -> List[RetrievalResult]:
        """
        Retrieve the most relevant code chunks for a query.
        
        Args:
            query: Search query string
            job_id: Job ID to search within
            top_k: Number of results to return
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of RetrievalResult objects ranked by relevance
            
        Raises:
            RetrieverError: If retrieval fails
        """
        top_k = top_k or settings.DEFAULT_TOP_K
        threshold = score_threshold or settings.SIMILARITY_THRESHOLD
        
        logger.info(f"Retrieving chunks for query in job {job_id}, top_k={top_k}")
        
        # Validate job exists
        job = JobRepository.get_job(job_id)
        if not job:
            raise RetrieverError(f"Job not found: {job_id}")
        
        # Check if embeddings exist for this job
        has_embeddings = await self._vector_store.has_embeddings(job_id)
        if not has_embeddings:
            logger.warning(f"No embeddings found for job {job_id}, generating now...")
            await self.embed_job_chunks(job_id)
        
        # Generate query embedding
        try:
            query_embedding = await self._embedding_service.generate_single_embedding(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise RetrieverError(f"Failed to generate query embedding: {e}")
        
        # Perform similarity search
        try:
            search_results = await self._vector_store.similarity_search(
                query_vector=query_embedding,
                job_id=job_id,
                top_k=top_k,
                score_threshold=threshold
            )
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise RetrieverError(f"Similarity search failed: {e}")
        
        # Convert to RetrievalResult objects
        results = [
            RetrievalResult(
                chunk_id=sr.chunk_id,
                file_path=sr.file_path,
                content=sr.content,
                score=sr.score,
                language=sr.language,
                start_line=sr.start_line,
                end_line=sr.end_line
            )
            for sr in search_results
        ]
        
        logger.info(f"Retrieved {len(results)} chunks for query")
        return results
    
    async def embed_job_chunks(self, job_id: str) -> int:
        """
        Generate and store embeddings for all chunks of a job.
        
        Args:
            job_id: Job ID to embed chunks for
            
        Returns:
            Number of chunks embedded
            
        Raises:
            RetrieverError: If embedding fails
        """
        logger.info(f"Embedding chunks for job {job_id}")
        
        # Get all chunks for the job
        chunks = ChunkRepository.get_chunks_by_job(job_id, limit=10000)
        
        if not chunks:
            logger.warning(f"No chunks found for job {job_id}")
            return 0
        
        logger.info(f"Found {len(chunks)} chunks to embed")
        
        # Prepare texts for embedding
        texts = [chunk.content for chunk in chunks]
        
        # Generate embeddings
        try:
            embeddings = await self._embedding_service.generate_embeddings(texts)
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise RetrieverError(f"Failed to generate embeddings: {e}")
        
        # Create embedding documents
        from src.embeddings.vector_store import EmbeddingDocument
        
        documents = []
        for chunk, embedding in zip(chunks, embeddings):
            doc = EmbeddingDocument(
                job_id=chunk.job_id,
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                content=chunk.content,
                embedding=embedding,
                language=chunk.language,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                metadata=chunk.metadata
            )
            documents.append(doc)
        
        # Store embeddings
        try:
            count = await self._vector_store.upsert_embeddings(documents)
            logger.info(f"Stored {count} embeddings for job {job_id}")
            return count
        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            raise RetrieverError(f"Failed to store embeddings: {e}")
    
    async def retrieve_with_context(
        self,
        query: str,
        job_id: str,
        top_k: int = None,
        include_surrounding: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks with additional context for RAG.
        
        Args:
            query: Search query string
            job_id: Job ID to search within
            top_k: Number of results to return
            include_surrounding: Include surrounding chunks for context
            
        Returns:
            List of dictionaries with chunk data and context
        """
        results = await self.retrieve(query, job_id, top_k)
        
        enriched_results = []
        for result in results:
            enriched = result.to_dict()
            
            # Add file context
            if include_surrounding:
                # Get surrounding chunks from the same file
                file_chunks = ChunkRepository.get_chunks_by_file(
                    job_id, result.file_path
                )
                
                # Find current chunk position
                chunk_index = None
                for i, fc in enumerate(file_chunks):
                    if fc.chunk_id == result.chunk_id:
                        chunk_index = i
                        break
                
                if chunk_index is not None:
                    # Add previous chunk if exists
                    if chunk_index > 0:
                        prev_chunk = file_chunks[chunk_index - 1]
                        enriched["context_before"] = prev_chunk.content[:500]
                    
                    # Add next chunk if exists
                    if chunk_index < len(file_chunks) - 1:
                        next_chunk = file_chunks[chunk_index + 1]
                        enriched["context_after"] = next_chunk.content[:500]
            
            enriched_results.append(enriched)
        
        return enriched_results
    
    async def get_embedding_stats(self, job_id: str) -> Dict[str, Any]:
        """
        Get embedding statistics for a job.
        
        Args:
            job_id: Job ID to check
            
        Returns:
            Dictionary with embedding stats
        """
        chunk_count = ChunkRepository.count_chunks_by_job(job_id)
        embedding_count = await self._vector_store.count_embeddings(job_id)
        
        return {
            "job_id": job_id,
            "total_chunks": chunk_count,
            "embedded_chunks": embedding_count,
            "embedding_coverage": (
                embedding_count / chunk_count if chunk_count > 0 else 0
            ),
            "is_complete": chunk_count == embedding_count
        }


# Module-level convenience functions
_retriever: Optional[Retriever] = None


def get_retriever() -> Retriever:
    """Get or create the global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


async def retrieve(
    query: str,
    job_id: str,
    top_k: int = None
) -> List[RetrievalResult]:
    """
    Convenience function to retrieve relevant chunks.
    
    Args:
        query: Search query
        job_id: Job ID to search
        top_k: Number of results
        
    Returns:
        List of RetrievalResult objects
    """
    retriever = get_retriever()
    return await retriever.retrieve(query, job_id, top_k)
