"""
API routes module for DocuMind AI.
Contains all route handlers organized by feature.
"""

from src.api.routes.ingestion import router as ingestion_router

__all__ = ["ingestion_router"]
