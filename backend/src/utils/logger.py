"""
Logging utility for DocuMind AI backend.
Provides consistent, formatted logging across all modules.

Phase 4: Added structured logging with request_id support.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any

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
        
        # Add exception info if present (only in development)
        if record.exc_info and not settings.is_production():
            formatted_msg += f"\n{self.formatException(record.exc_info)}"
            
        return formatted_msg


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in production."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'job_id'):
            log_entry["job_id"] = record.job_id
        if hasattr(record, 'endpoint'):
            log_entry["endpoint"] = record.endpoint
        
        # Add exception info
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }
            # Only include stack trace in development
            if not settings.is_production():
                log_entry["exception"]["traceback"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class PlainFormatter(logging.Formatter):
    """Plain text formatter without colors."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as plain text."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = f"[{timestamp}] [{record.levelname}] [{record.name}] {record.getMessage()}"
        
        if record.exc_info and not settings.is_production():
            msg += f"\n{self.formatException(record.exc_info)}"
        
        return msg


def get_formatter() -> logging.Formatter:
    """Get the appropriate formatter based on configuration."""
    log_format = settings.LOG_FORMAT.lower()
    
    if log_format == "json" or settings.is_production():
        return JSONFormatter()
    elif log_format == "plain":
        return PlainFormatter()
    else:
        return ColoredFormatter()


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
        # Set log level - in production, minimum is INFO (no DEBUG)
        if settings.is_production():
            log_level = max(
                getattr(logging, level or settings.LOG_LEVEL, logging.INFO),
                logging.INFO
            )
        else:
            log_level = getattr(logging, level or settings.LOG_LEVEL, logging.INFO)
        
        logger.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(get_formatter())
        
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds structured context to log messages."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra context to log record."""
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs


def get_structured_logger(
    name: str,
    request_id: Optional[str] = None,
    job_id: Optional[str] = None,
    **extra_context
) -> StructuredLoggerAdapter:
    """
    Get a logger with structured context.
    
    Args:
        name: Logger name
        request_id: Request ID for tracing
        job_id: Job ID for job-related logs
        **extra_context: Additional context fields
        
    Returns:
        Logger adapter with context
    """
    base_logger = get_logger(name)
    context = {
        k: v for k, v in {
            'request_id': request_id,
            'job_id': job_id,
            **extra_context
        }.items() if v is not None
    }
    return StructuredLoggerAdapter(base_logger, context)


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
