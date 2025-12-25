"""
Embeddings module for DocuMind AI.
Phase 2: Vector Embedding Generation & Storage.

This module provides:
- EmbeddingService: Generate vector embeddings from text (OpenAI or mock)
- VectorStore: Store embeddings in MongoDB Atlas and perform similarity search
"""

from src.embeddings.embedding_service import EmbeddingService
from src.embeddings.vector_store import VectorStore

__all__ = ["EmbeddingService", "VectorStore"]
