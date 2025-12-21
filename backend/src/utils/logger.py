"""
Logging utility for DocuMind AI backend.
Provides consistent, formatted logging across all modules.
"""

import logging
import sys
from datetime import datetime
from typing import Optional

from src.config import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for different log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[41m',  # Red background
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color based on level."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format the message
        formatted_msg = (
            f"{color}[{timestamp}] [{record.levelname}] "
            f"[{record.name}]{reset} {record.getMessage()}"
        )
        
        # Add exception info if present
        if record.exc_info:
            formatted_msg += f"\n{self.formatException(record.exc_info)}"
            
        return formatted_msg


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Set log level
        log_level = getattr(logging, level or settings.LOG_LEVEL, logging.INFO)
        logger.setLevel(log_level)
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(ColoredFormatter())
        
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger


# Pre-configured loggers for common modules
def get_ingestion_logger() -> logging.Logger:
    """Get logger for ingestion module."""
    return get_logger("documind.ingestion")


def get_database_logger() -> logging.Logger:
    """Get logger for database module."""
    return get_logger("documind.database")


def get_api_logger() -> logging.Logger:
    """Get logger for API module."""
    return get_logger("documind.api")
