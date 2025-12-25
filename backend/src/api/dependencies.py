"""
FastAPI dependencies for DocuMind AI.
Provides dependency injection for database connections and services.
"""

from typing import Generator
from pymongo.database import Database

from src.database.mongodb import get_db


def get_database() -> Generator[Database, None, None]:
    """
    Dependency to get database connection.
    
    Yields:
        Database instance
    """
    db = get_db()
    yield db
