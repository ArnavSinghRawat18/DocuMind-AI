"""
MongoDB connection management for DocuMind AI backend.
Provides connection pooling and database access.
"""

from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from src.config import settings
from src.utils.logger import get_database_logger

logger = get_database_logger()


class MongoDB:
    """
    MongoDB connection manager with singleton pattern.
    Handles connection pooling and provides access to the database.
    """
    
    _instance: Optional['MongoDB'] = None
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None
    
    def __new__(cls) -> 'MongoDB':
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self) -> Database:
        """
        Establish connection to MongoDB.
        
        Returns:
            Database instance
            
        Raises:
            ConnectionFailure: If connection cannot be established
        """
        if self._database is not None:
            return self._database
        
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}")
            
            # Create client with connection pooling
            self._client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                maxPoolSize=50,
                minPoolSize=10
            )
            
            # Verify connection
            self._client.admin.command('ping')
            
            # Get database
            self._database = self._client[settings.MONGODB_DATABASE]
            
            logger.info(f"Connected to MongoDB database: {settings.MONGODB_DATABASE}")
            
            # Create indexes for better query performance
            self._create_indexes()
            
            return self._database
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ConnectionFailure(f"Could not connect to MongoDB: {e}")
    
    def _create_indexes(self) -> None:
        """Create indexes for optimal query performance."""
        try:
            # Jobs collection indexes
            jobs_collection = self._database[settings.JOBS_COLLECTION]
            jobs_collection.create_index("job_id", unique=True)
            jobs_collection.create_index("status")
            jobs_collection.create_index("created_at")
            
            # Code chunks collection indexes
            chunks_collection = self._database[settings.CHUNKS_COLLECTION]
            chunks_collection.create_index("job_id")
            chunks_collection.create_index("chunk_id", unique=True)
            chunks_collection.create_index([("job_id", 1), ("file_path", 1)])
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
    
    def get_database(self) -> Database:
        """
        Get the database instance, connecting if necessary.
        
        Returns:
            Database instance
        """
        if self._database is None:
            return self.connect()
        return self._database
    
    def get_collection(self, collection_name: str):
        """
        Get a collection from the database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection instance
        """
        db = self.get_database()
        return db[collection_name]
    
    def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")
    
    def is_connected(self) -> bool:
        """
        Check if the database connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        if self._client is None:
            return False
        
        try:
            self._client.admin.command('ping')
            return True
        except Exception:
            return False


# Global database instance
db = MongoDB()


def get_db() -> Database:
    """
    Get the database instance.
    Convenience function for dependency injection.
    
    Returns:
        Database instance
    """
    return db.get_database()


def get_jobs_collection():
    """Get the jobs collection."""
    return db.get_collection(settings.JOBS_COLLECTION)


def get_chunks_collection():
    """Get the code chunks collection."""
    return db.get_collection(settings.CHUNKS_COLLECTION)
