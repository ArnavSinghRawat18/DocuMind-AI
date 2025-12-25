"""
Ingestion module for DocuMind AI.
Handles git cloning, file scanning, parsing, and chunking.
"""

from src.ingestion.git_client import GitClient, GitClientError, clone_repo
from src.ingestion.file_walker import FileWalker, FileInfo, scan_repository
from src.ingestion.parser import FileParser, ParsedFile, FileParseError, parse_file
from src.ingestion.chunker import TextChunker, Chunk, chunk_parsed_file, chunk_text

__all__ = [
    # Git Client
    "GitClient",
    "GitClientError",
    "clone_repo",
    # File Walker
    "FileWalker",
    "FileInfo",
    "scan_repository",
    # Parser
    "FileParser",
    "ParsedFile",
    "FileParseError",
    "parse_file",
    # Chunker
    "TextChunker",
    "Chunk",
    "chunk_parsed_file",
    "chunk_text",
]
