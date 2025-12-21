"""
File parser for reading and processing source code files.
Handles encoding detection and provides clean text with metadata.
"""

import codecs
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from src.ingestion.file_walker import FileInfo, get_language_from_extension
from src.utils.logger import get_ingestion_logger

logger = get_ingestion_logger()


# Common encodings to try in order of likelihood
ENCODINGS_TO_TRY = [
    'utf-8',
    'utf-8-sig',  # UTF-8 with BOM
    'latin-1',    # ISO-8859-1, handles most Western European text
    'cp1252',     # Windows Western European
    'ascii',
]


@dataclass
class ParsedFile:
    """Result of parsing a source file."""
    file_path: str          # Relative path
    absolute_path: str      # Absolute path
    content: str            # File content as string
    language: str           # Detected language
    total_lines: int        # Total line count
    encoding: str           # Detected encoding
    size_bytes: int         # File size in bytes


class FileParseError(Exception):
    """Custom exception for file parsing errors."""
    pass


class FileParser:
    """
    Parser for reading source code files with encoding detection.
    """
    
    def __init__(self):
        """Initialize the file parser."""
        pass
    
    def parse_file(self, file_info: FileInfo) -> ParsedFile:
        """
        Parse a source file and return its contents with metadata.
        
        Args:
            file_info: FileInfo object from file walker
            
        Returns:
            ParsedFile object with content and metadata
            
        Raises:
            FileParseError: If file cannot be read
        """
        file_path = Path(file_info.absolute_path)
        
        if not file_path.exists():
            raise FileParseError(f"File not found: {file_info.absolute_path}")
        
        if not file_path.is_file():
            raise FileParseError(f"Not a file: {file_info.absolute_path}")
        
        # Try to read file with encoding detection
        content, encoding = self._read_with_encoding_detection(file_path)
        
        # Clean the content
        content = self._clean_content(content)
        
        # Count lines
        total_lines = content.count('\n') + 1 if content else 0
        
        # Detect language from extension
        language = get_language_from_extension(file_info.extension)
        
        return ParsedFile(
            file_path=file_info.relative_path,
            absolute_path=file_info.absolute_path,
            content=content,
            language=language,
            total_lines=total_lines,
            encoding=encoding,
            size_bytes=file_info.size_bytes
        )
    
    def _read_with_encoding_detection(
        self, 
        file_path: Path
    ) -> Tuple[str, str]:
        """
        Read file content with automatic encoding detection.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (content, detected_encoding)
            
        Raises:
            FileParseError: If file cannot be decoded
        """
        # First, try to detect encoding from file content
        raw_content = file_path.read_bytes()
        
        # Check for BOM markers
        if raw_content.startswith(codecs.BOM_UTF8):
            try:
                return raw_content[3:].decode('utf-8'), 'utf-8-sig'
            except UnicodeDecodeError:
                pass
        
        if raw_content.startswith(codecs.BOM_UTF16_LE):
            try:
                return raw_content[2:].decode('utf-16-le'), 'utf-16-le'
            except UnicodeDecodeError:
                pass
        
        if raw_content.startswith(codecs.BOM_UTF16_BE):
            try:
                return raw_content[2:].decode('utf-16-be'), 'utf-16-be'
            except UnicodeDecodeError:
                pass
        
        # Try common encodings
        for encoding in ENCODINGS_TO_TRY:
            try:
                content = raw_content.decode(encoding)
                return content, encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Last resort: decode with errors='replace'
        logger.warning(
            f"Could not detect encoding for {file_path}, using utf-8 with replacement"
        )
        content = raw_content.decode('utf-8', errors='replace')
        return content, 'utf-8-fallback'
    
    def _clean_content(self, content: str) -> str:
        """
        Clean file content for processing.
        
        Args:
            content: Raw file content
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
        
        # Normalize line endings to \n
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove null bytes (sometimes appear in corrupted files)
        content = content.replace('\x00', '')
        
        # Remove other problematic control characters (keep newlines and tabs)
        cleaned_chars = []
        for char in content:
            if char in '\n\t' or (ord(char) >= 32 and ord(char) != 127):
                cleaned_chars.append(char)
            elif ord(char) < 32:
                # Replace other control chars with space
                cleaned_chars.append(' ')
        
        content = ''.join(cleaned_chars)
        
        # Remove trailing whitespace from each line
        lines = content.split('\n')
        lines = [line.rstrip() for line in lines]
        content = '\n'.join(lines)
        
        # Ensure file ends with newline
        if content and not content.endswith('\n'):
            content += '\n'
        
        return content
    
    def parse_file_from_path(
        self, 
        absolute_path: str,
        relative_path: str
    ) -> ParsedFile:
        """
        Parse a file directly from its path.
        
        Args:
            absolute_path: Absolute path to file
            relative_path: Relative path for metadata
            
        Returns:
            ParsedFile object
        """
        file_path = Path(absolute_path)
        
        if not file_path.exists():
            raise FileParseError(f"File not found: {absolute_path}")
        
        # Create FileInfo manually
        file_info = FileInfo(
            absolute_path=absolute_path,
            relative_path=relative_path,
            extension=file_path.suffix.lower(),
            size_bytes=file_path.stat().st_size
        )
        
        return self.parse_file(file_info)


def count_tokens_approximate(text: str) -> int:
    """
    Approximate token count for a text string.
    Uses a simple heuristic based on whitespace and punctuation.
    
    For more accurate counting, consider using tiktoken library.
    
    Args:
        text: Input text
        
    Returns:
        Approximate token count
    """
    if not text:
        return 0
    
    # Simple approximation: ~4 characters per token for code
    # This is a rough estimate; actual tokenization varies by model
    char_count = len(text)
    
    # Adjust for code-specific patterns
    # Code tends to have more tokens per character due to symbols
    word_count = len(text.split())
    
    # Use average of character-based and word-based estimates
    char_based = char_count / 4
    word_based = word_count * 1.3  # Words in code often split into multiple tokens
    
    return int((char_based + word_based) / 2)


# Module-level convenience function
def parse_file(file_info: FileInfo) -> ParsedFile:
    """
    Convenience function to parse a file.
    
    Args:
        file_info: FileInfo object
        
    Returns:
        ParsedFile object
    """
    parser = FileParser()
    return parser.parse_file(file_info)
