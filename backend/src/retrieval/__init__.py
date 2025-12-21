"""
Retrieval module for DocuMind AI.
Phase 2: RAG Retrieval Pipeline.

This module provides:
- Retriever: Combine embedding generation and vector search for RAG
- Query processing and context retrieval
- Semantic search across code chunks
"""

from src.retrieval.retriever import Retriever

__all__ = ["Retriever"]
