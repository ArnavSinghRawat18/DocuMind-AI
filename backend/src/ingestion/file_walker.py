"""
File walker for recursively scanning repository directories.
Filters files by extension and ignores specified directories.
"""

import os
from pathlib import Path
from typing import List, Set, Generator, Optional
from dataclasses import dataclass

from src.config import settings
from src.utils.logger import get_ingestion_logger

logger = get_ingestion_logger()


@dataclass
class FileInfo:
    """Information about a discovered file."""
    absolute_path: str
    relative_path: str
    extension: str
    size_bytes: int


class FileWalker:
    """
    Recursively walks a directory and yields files matching criteria.
    Respects ignore patterns and allowed file extensions.
    """
    
    def __init__(
        self,
        allowed_extensions: Optional[Set[str]] = None,
        ignored_directories: Optional[Set[str]] = None,
        max_file_size_mb: float = 10.0
    ):
        """
        Initialize FileWalker with filtering criteria.
        
        Args:
            allowed_extensions: Set of allowed file extensions (e.g., {'.py', '.js'})
            ignored_directories: Set of directory names to ignore
            max_file_size_mb: Maximum file size in MB to process
        """
        self.allowed_extensions = allowed_extensions or settings.ALLOWED_EXTENSIONS
        self.ignored_directories = ignored_directories or settings.IGNORED_DIRECTORIES
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
    
    def walk(self, root_path: str) -> Generator[FileInfo, None, None]:
        """
        Walk directory tree and yield matching files.
        
        Args:
            root_path: Root directory to start walking from
            
        Yields:
            FileInfo objects for each matching file
        """
        root = Path(root_path)
        
        if not root.exists():
            logger.error(f"Directory does not exist: {root_path}")
            return
        
        if not root.is_dir():
            logger.error(f"Path is not a directory: {root_path}")
            return
        
        logger.info(f"Scanning directory: {root_path}")
        logger.debug(f"Allowed extensions: {self.allowed_extensions}")
        logger.debug(f"Ignored directories: {self.ignored_directories}")
        
        file_count = 0
        skipped_count = 0
        
        for dirpath, dirnames, filenames in os.walk(root):
            # Filter out ignored directories (modifying in-place to skip traversal)
            dirnames[:] = [
                d for d in dirnames 
                if d not in self.ignored_directories and not d.startswith('.')
            ]
            
            current_path = Path(dirpath)
            
            for filename in filenames:
                file_path = current_path / filename
                
                # Check file extension
                ext = file_path.suffix.lower()
                if ext not in self.allowed_extensions:
                    skipped_count += 1
                    continue
                
                # Check if file exists and is readable
                if not file_path.is_file():
                    continue
                
                try:
                    # Get file size
                    file_size = file_path.stat().st_size
                    
                    # Skip files that are too large
                    if file_size > self.max_file_size_bytes:
                        logger.warning(
                            f"Skipping large file ({file_size / 1024 / 1024:.2f}MB): "
                            f"{file_path}"
                        )
                        skipped_count += 1
                        continue
                    
                    # Skip empty files
                    if file_size == 0:
                        skipped_count += 1
                        continue
                    
                    # Calculate relative path
                    relative_path = str(file_path.relative_to(root))
                    # Normalize path separators to forward slashes
                    relative_path = relative_path.replace('\\', '/')
                    
                    file_count += 1
                    
                    yield FileInfo(
                        absolute_path=str(file_path),
                        relative_path=relative_path,
                        extension=ext,
                        size_bytes=file_size
                    )
                    
                except OSError as e:
                    logger.warning(f"Could not access file {file_path}: {e}")
                    continue
        
        logger.info(
            f"Scan complete: found {file_count} files, skipped {skipped_count} files"
        )
    
    def get_all_files(self, root_path: str) -> List[FileInfo]:
        """
        Get all matching files as a list.
        
        Args:
            root_path: Root directory to scan
            
        Returns:
            List of FileInfo objects
        """
        return list(self.walk(root_path))
    
    def count_files(self, root_path: str) -> dict:
        """
        Count files by extension in a directory.
        
        Args:
            root_path: Root directory to scan
            
        Returns:
            Dictionary with extension counts and total
        """
        counts = {
            "total": 0,
            "by_extension": {}
        }
        
        for file_info in self.walk(root_path):
            counts["total"] += 1
            ext = file_info.extension
            counts["by_extension"][ext] = counts["by_extension"].get(ext, 0) + 1
        
        return counts


def get_extension_language_map() -> dict:
    """
    Get mapping of file extensions to programming languages.
    
    Returns:
        Dictionary mapping extensions to language names
    """
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".md": "markdown",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".json": "json",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
        ".sh": "bash",
        ".bash": "bash",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
    }


def get_language_from_extension(extension: str) -> str:
    """
    Get programming language name from file extension.
    
    Args:
        extension: File extension (e.g., '.py')
        
    Returns:
        Language name or 'unknown'
    """
    ext_map = get_extension_language_map()
    return ext_map.get(extension.lower(), "unknown")


# Module-level convenience function
def scan_repository(repo_path: str) -> List[FileInfo]:
    """
    Convenience function to scan a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        List of FileInfo objects
    """
    walker = FileWalker()
    return walker.get_all_files(repo_path)
