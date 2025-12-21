"""
Embedding service for DocuMind AI.
Generates vector embeddings from text using Hugging Face or mock embeddings.
"""

import asyncio
import hashlib
import math
from typing import List, Optional, Union
from abc import ABC, abstractmethod

import numpy as np

from src.config import settings
from src.utils.logger import get_logger
from src.embeddings.hf_provider import HFEmbeddingProvider

logger = get_logger("documind.embeddings")


class EmbeddingError(Exception):
    """Custom exception for embedding generation errors."""
    pass


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    async def generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        pass


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Mock embedding provider for testing without API calls.
    Generates deterministic pseudo-random embeddings based on text hash.
    """
    
    def __init__(self, dimensions: int = 1536):
        self._dimensions = dimensions
        logger.info(f"Initialized MockEmbeddingProvider with {dimensions} dimensions")
    
    @property
    def dimensions(self) -> int:
        return self._dimensions
    
    async def generate(self, texts: List[str]) -> List[List[float]]:
        """
        Generate deterministic mock embeddings based on text hash.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        logger.debug(f"Generating mock embeddings for {len(texts)} texts")
        
        embeddings = []
        for text in texts:
            # Create deterministic seed from text hash
            text_hash = hashlib.md5(text.encode()).hexdigest()
            seed = int(text_hash[:8], 16)
            
            # Generate pseudo-random embedding
            np.random.seed(seed)
            embedding = np.random.randn(self._dimensions).astype(np.float32)
            
            # Normalize to unit vector (L2 normalization)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            embeddings.append(embedding.tolist())
        
        return embeddings


class HFEmbeddingProviderWrapper(BaseEmbeddingProvider):
    """
    Async wrapper for HFEmbeddingProvider to conform to BaseEmbeddingProvider interface.
    Uses Hugging Face Inference API for embeddings.
    """
    
    def __init__(self, api_key: str, model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._hf_provider = HFEmbeddingProvider(api_key=api_key, model=model)
        self._dimensions = 384  # HF model output dimensions
        logger.info(f"Initialized HFEmbeddingProviderWrapper with model {model}")
    
    @property
    def dimensions(self) -> int:
        return self._dimensions
    
    async def generate(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Hugging Face API.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        logger.debug(f"Generating HF embeddings for {len(texts)} texts")
        
        try:
            # Run synchronous HF provider in executor to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, self._hf_provider.embed, texts
            )
            return embeddings
        except RuntimeError as e:
            logger.error(f"HF embedding error: {e}")
            raise EmbeddingError(f"Failed to generate embeddings: {e}")


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI embedding provider using the OpenAI API.
    NOTE: This provider is deprecated. Use HFEmbeddingProviderWrapper instead.
    """
    
    def __init__(
        self, 
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536
    ):
        self._dimensions = dimensions
        self._model = model
        self._api_key = api_key
        
        # Import openai here to make it optional
        try:
            import openai
            self._client = openai.AsyncOpenAI(api_key=api_key)
            logger.info(f"Initialized OpenAIEmbeddingProvider with model {model}")
        except ImportError:
            raise EmbeddingError(
                "OpenAI package not installed. Install with: pip install openai"
            )
    
    @property
    def dimensions(self) -> int:
        return self._dimensions
    
    async def generate(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using OpenAI API.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        logger.debug(f"Generating OpenAI embeddings for {len(texts)} texts")
        
        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=texts,
                dimensions=self._dimensions
            )
            
            # Extract embeddings in correct order
            embeddings = [None] * len(texts)
            for item in response.data:
                embeddings[item.index] = item.embedding
            
            return embeddings
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise EmbeddingError(f"Failed to generate embeddings: {e}")


class EmbeddingService:
    """
    Main embedding service for generating and managing text embeddings.
    Supports batch processing, normalization, and provider abstraction.
    """
    
    def __init__(
        self,
        provider: Optional[BaseEmbeddingProvider] = None,
        batch_size: int = None
    ):
        """
        Initialize the embedding service.
        
        Args:
            provider: Embedding provider (defaults based on settings)
            batch_size: Maximum texts per batch (default from settings)
        """
        self.batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        
        # Initialize provider based on settings
        if provider:
            self._provider = provider
        elif settings.USE_MOCK_EMBEDDINGS:
            logger.info("Using mock embedding provider")
            self._provider = MockEmbeddingProvider(
                dimensions=settings.EMBEDDING_DIMENSIONS
            )
        else:
            logger.info("Using Hugging Face embedding provider")
            self._provider = HFEmbeddingProviderWrapper(
                api_key=settings.HF_API_KEY,
                model=settings.HF_EMBEDDING_MODEL
            )
    
    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._provider.dimensions
    
    async def generate_embeddings(
        self, 
        texts: Union[str, List[str]],
        normalize: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for one or more texts.
        
        Args:
            texts: Single text or list of texts to embed
            normalize: Whether to L2 normalize embeddings (default True)
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        # Handle single text input
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Clean and validate texts
        cleaned_texts = [self._clean_text(t) for t in texts]
        
        # Process in batches for large inputs
        all_embeddings = []
        
        for i in range(0, len(cleaned_texts), self.batch_size):
            batch = cleaned_texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = math.ceil(len(cleaned_texts) / self.batch_size)
            
            logger.debug(f"Processing batch {batch_num}/{total_batches}")
            
            try:
                batch_embeddings = await self._provider.generate(batch)
                
                # Normalize if requested
                if normalize:
                    batch_embeddings = [
                        self._normalize_l2(emb) for emb in batch_embeddings
                    ]
                
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Batch {batch_num} failed: {e}")
                raise EmbeddingError(f"Embedding generation failed at batch {batch_num}: {e}")
        
        logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
        return all_embeddings
    
    async def generate_single_embedding(
        self, 
        text: str,
        normalize: bool = True
    ) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            normalize: Whether to L2 normalize (default True)
            
        Returns:
            Single embedding vector
        """
        embeddings = await self.generate_embeddings([text], normalize=normalize)
        return embeddings[0] if embeddings else []
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text before embedding.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate very long texts (OpenAI has ~8k token limit)
        max_chars = 30000  # Roughly 8k tokens
        if len(text) > max_chars:
            logger.warning(f"Truncating text from {len(text)} to {max_chars} chars")
            text = text[:max_chars]
        
        return text
    
    @staticmethod
    def _normalize_l2(embedding: List[float]) -> List[float]:
        """
        L2 normalize an embedding vector.
        
        Args:
            embedding: Raw embedding vector
            
        Returns:
            Normalized embedding vector
        """
        arr = np.array(embedding, dtype=np.float32)
        norm = np.linalg.norm(arr)
        
        if norm > 0:
            arr = arr / norm
        
        return arr.tolist()
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0 to 1 for normalized vectors)
        """
        arr1 = np.array(vec1, dtype=np.float32)
        arr2 = np.array(vec2, dtype=np.float32)
        
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


# Module-level convenience functions
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def generate_embeddings(texts: Union[str, List[str]]) -> List[List[float]]:
    """
    Convenience function to generate embeddings.
    
    Args:
        texts: Text or list of texts to embed
        
    Returns:
        List of embedding vectors
    """
    service = get_embedding_service()
    return await service.generate_embeddings(texts)
