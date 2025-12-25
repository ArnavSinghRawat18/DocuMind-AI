"""
Vector store for DocuMind AI using MongoDB Atlas Vector Search.
Handles storage and retrieval of vector embeddings.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from pymongo import UpdateOne
from pymongo.errors import BulkWriteError, OperationFailure

from src.config import settings
from src.database.mongodb import db
from src.utils.logger import get_logger

logger = get_logger("documind.vector_store")


@dataclass
class EmbeddingDocument:
    """Represents an embedding document in the vector store."""
    job_id: str
    chunk_id: str
    file_path: str
    content: str
    embedding: List[float]
    language: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
    def to_mongo_dict(self) -> Dict[str, Any]:
        """Convert to MongoDB document format."""
        doc = {
            "job_id": self.job_id,
            "chunk_id": self.chunk_id,
            "file_path": self.file_path,
            "content": self.content,
            "embedding": self.embedding,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "metadata": self.metadata or {},
            "created_at": self.created_at or datetime.utcnow()
        }
        return doc


@dataclass
class SearchResult:
    """Represents a vector search result."""
    chunk_id: str
    job_id: str
    file_path: str
    content: str
    score: float
    language: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class VectorStoreError(Exception):
    """Custom exception for vector store operations."""
    pass


class VectorStore:
    """
    MongoDB Atlas Vector Search store for embeddings.
    
    Stores embeddings with metadata and provides similarity search capabilities.
    Uses MongoDB Atlas Vector Search index for efficient nearest neighbor queries.
    """
    
    def __init__(self, collection_name: str = None):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the embeddings collection
        """
        self.collection_name = collection_name or settings.EMBEDDINGS_COLLECTION
        self._collection = None
        self._index_name = settings.VECTOR_SEARCH_INDEX_NAME
        
        logger.info(f"Initialized VectorStore with collection: {self.collection_name}")
    
    @property
    def collection(self):
        """Get the MongoDB collection, lazily initialized."""
        if self._collection is None:
            self._collection = db.get_collection(self.collection_name)
            self._ensure_indexes()
        return self._collection
    
    def _ensure_indexes(self) -> None:
        """Create necessary indexes for the embeddings collection."""
        try:
            # Standard indexes for filtering
            self._collection.create_index("job_id")
            self._collection.create_index("chunk_id", unique=True)
            self._collection.create_index([("job_id", 1), ("file_path", 1)])
            
            logger.info("Standard indexes created for embeddings collection")
            
            # Note: Atlas Vector Search index must be created via Atlas UI or API
            # The index definition would be:
            # {
            #   "fields": [{
            #     "type": "vector",
            #     "path": "embedding",
            #     "numDimensions": 1536,
            #     "similarity": "cosine"
            #   }]
            # }
            
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
    
    async def upsert_embeddings(
        self, 
        documents: List[EmbeddingDocument]
    ) -> int:
        """
        Insert or update embeddings in the vector store.
        
        Args:
            documents: List of EmbeddingDocument objects
            
        Returns:
            Number of documents upserted
        """
        if not documents:
            return 0
        
        logger.info(f"Upserting {len(documents)} embeddings")
        
        # Build bulk upsert operations
        operations = []
        for doc in documents:
            operations.append(
                UpdateOne(
                    {"chunk_id": doc.chunk_id},
                    {"$set": doc.to_mongo_dict()},
                    upsert=True
                )
            )
        
        try:
            result = self.collection.bulk_write(operations, ordered=False)
            
            upserted = result.upserted_count + result.modified_count
            logger.info(
                f"Upsert complete: {result.upserted_count} inserted, "
                f"{result.modified_count} modified"
            )
            return upserted
            
        except BulkWriteError as e:
            logger.error(f"Bulk write error: {e.details}")
            # Return partial success count
            return e.details.get('nUpserted', 0) + e.details.get('nModified', 0)
        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            raise VectorStoreError(f"Failed to upsert embeddings: {e}")
    
    async def similarity_search(
        self,
        query_vector: List[float],
        job_id: str,
        top_k: int = 5,
        score_threshold: float = None
    ) -> List[SearchResult]:
        """
        Perform vector similarity search using MongoDB Atlas Vector Search.
        
        Args:
            query_vector: Query embedding vector
            job_id: Filter results to this job
            top_k: Number of results to return
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of SearchResult objects ranked by similarity
        """
        logger.info(f"Performing similarity search for job {job_id}, top_k={top_k}")
        
        threshold = score_threshold or settings.SIMILARITY_THRESHOLD
        
        # Try Atlas Vector Search first
        try:
            results = await self._atlas_vector_search(
                query_vector, job_id, top_k, threshold
            )
            if results:
                return results
        except OperationFailure as e:
            # Atlas Vector Search index may not exist
            logger.warning(f"Atlas Vector Search failed: {e}")
            logger.info("Falling back to in-memory cosine similarity search")
        
        # Fallback to in-memory search (less efficient but works without Atlas index)
        return await self._fallback_similarity_search(
            query_vector, job_id, top_k, threshold
        )
    
    async def _atlas_vector_search(
        self,
        query_vector: List[float],
        job_id: str,
        top_k: int,
        score_threshold: float
    ) -> List[SearchResult]:
        """
        Perform search using MongoDB Atlas Vector Search aggregation.
        
        Args:
            query_vector: Query embedding vector
            job_id: Filter results to this job
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of SearchResult objects
        """
        # Atlas Vector Search aggregation pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": self._index_name,
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": top_k * 10,  # Search more candidates for better results
                    "limit": top_k,
                    "filter": {"job_id": job_id}
                }
            },
            {
                "$project": {
                    "chunk_id": 1,
                    "job_id": 1,
                    "file_path": 1,
                    "content": 1,
                    "language": 1,
                    "start_line": 1,
                    "end_line": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        results = []
        cursor = self.collection.aggregate(pipeline)
        
        for doc in cursor:
            score = doc.get("score", 0)
            
            # Apply score threshold
            if score < score_threshold:
                continue
            
            results.append(SearchResult(
                chunk_id=doc["chunk_id"],
                job_id=doc["job_id"],
                file_path=doc["file_path"],
                content=doc["content"],
                score=score,
                language=doc.get("language"),
                start_line=doc.get("start_line"),
                end_line=doc.get("end_line"),
                metadata=doc.get("metadata")
            ))
        
        logger.info(f"Atlas Vector Search returned {len(results)} results")
        return results
    
    async def _fallback_similarity_search(
        self,
        query_vector: List[float],
        job_id: str,
        top_k: int,
        score_threshold: float
    ) -> List[SearchResult]:
        """
        Fallback in-memory cosine similarity search.
        Used when Atlas Vector Search index is not available.
        
        Args:
            query_vector: Query embedding vector
            job_id: Filter results to this job
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of SearchResult objects
        """
        import numpy as np
        
        # Fetch all embeddings for the job
        cursor = self.collection.find(
            {"job_id": job_id},
            {"chunk_id": 1, "job_id": 1, "file_path": 1, "content": 1,
             "embedding": 1, "language": 1, "start_line": 1, "end_line": 1,
             "metadata": 1}
        )
        
        query_arr = np.array(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query_arr)
        
        if query_norm == 0:
            return []
        
        query_arr = query_arr / query_norm
        
        # Calculate similarities
        scored_results = []
        for doc in cursor:
            embedding = doc.get("embedding", [])
            if not embedding:
                continue
            
            doc_arr = np.array(embedding, dtype=np.float32)
            doc_norm = np.linalg.norm(doc_arr)
            
            if doc_norm > 0:
                doc_arr = doc_arr / doc_norm
                score = float(np.dot(query_arr, doc_arr))
                
                if score >= score_threshold:
                    scored_results.append((score, doc))
        
        # Sort by score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Take top_k results
        results = []
        for score, doc in scored_results[:top_k]:
            results.append(SearchResult(
                chunk_id=doc["chunk_id"],
                job_id=doc["job_id"],
                file_path=doc["file_path"],
                content=doc["content"],
                score=score,
                language=doc.get("language"),
                start_line=doc.get("start_line"),
                end_line=doc.get("end_line"),
                metadata=doc.get("metadata")
            ))
        
        logger.info(f"Fallback search returned {len(results)} results")
        return results
    
    async def get_embeddings_by_job(
        self, 
        job_id: str, 
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get all embeddings for a job.
        
        Args:
            job_id: Job identifier
            limit: Maximum documents to return
            
        Returns:
            List of embedding documents
        """
        cursor = self.collection.find(
            {"job_id": job_id}
        ).limit(limit)
        
        return list(cursor)
    
    async def count_embeddings(self, job_id: str) -> int:
        """
        Count embeddings for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Number of embeddings
        """
        return self.collection.count_documents({"job_id": job_id})
    
    async def delete_embeddings_by_job(self, job_id: str) -> int:
        """
        Delete all embeddings for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Number of documents deleted
        """
        result = self.collection.delete_many({"job_id": job_id})
        logger.info(f"Deleted {result.deleted_count} embeddings for job {job_id}")
        return result.deleted_count
    
    async def has_embeddings(self, job_id: str) -> bool:
        """
        Check if embeddings exist for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if embeddings exist
        """
        return self.collection.count_documents({"job_id": job_id}, limit=1) > 0


# Module-level convenience functions
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
