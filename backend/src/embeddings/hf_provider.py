"""
Hugging Face embedding provider for DocuMind AI.
Generates vector embeddings locally using sentence-transformers.
"""

from typing import List

from sentence_transformers import SentenceTransformer

from src.utils.logger import get_logger

logger = get_logger("documind.embeddings.hf")


class HFEmbeddingProvider:
    """
    Local Hugging Face embedding provider using sentence-transformers.
    Generates 384-dimension embeddings offline without API calls.
    """
    
    def __init__(self, api_key: str = None, model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the local sentence-transformers embedding provider.
        
        Args:
            api_key: Ignored (kept for backward compatibility)
            model: Model identifier for sentence-transformers
        """
        self._model_name = model
        logger.info(f"Loading local sentence-transformers model: {model}")
        
        # Load model locally
        self._model = SentenceTransformer(model)
        self._dimensions = 384
        
        logger.info(f"Initialized HFEmbeddingProvider with local model {model}")
    
    @property
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        return self._dimensions
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using local model.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of 384-dimension normalized embedding vectors
        """
        if not texts:
            logger.debug("Empty text list provided, returning empty embeddings")
            return []
        
        # Ensure texts is a list
        if not isinstance(texts, list):
            texts = [texts]
        
        logger.info(f"Generating local embeddings for {len(texts)} texts")
        
        # Generate embeddings locally with L2 normalization
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        
        # Convert numpy arrays to list of lists
        result = embeddings.tolist()
        
        logger.info(f"Successfully generated {len(result)} embeddings")
        return result
