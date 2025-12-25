"""
Text chunker for splitting source code into manageable chunks.
Chunks are designed to fit within LLM context windows.
"""

import uuid
from typing import List, Optional
from dataclasses import dataclass

from src.config import settings
from src.ingestion.parser import ParsedFile, count_tokens_approximate
from src.utils.logger import get_ingestion_logger

logger = get_ingestion_logger()


@dataclass
class Chunk:
    """Represents a chunk of code/text."""
    chunk_id: str           # Unique chunk identifier
    job_id: str             # Parent job ID
    file_path: str          # Relative file path
    language: str           # Programming language
    start_line: int         # Starting line number (1-indexed)
    end_line: int           # Ending line number (1-indexed)
    content: str            # Chunk content
    token_count: int        # Approximate token count
    
    def to_dict(self) -> dict:
        """Convert chunk to dictionary for MongoDB storage."""
        return {
            "chunk_id": self.chunk_id,
            "job_id": self.job_id,
            "file_path": self.file_path,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "token_count": self.token_count,
            "metadata": {
                "line_count": self.end_line - self.start_line + 1
            }
        }


class TextChunker:
    """
    Splits source code into chunks of approximately max_tokens size.
    Respects line boundaries and attempts to split at logical points.
    """
    
    def __init__(
        self,
        max_tokens: int = None,
        overlap_lines: int = None
    ):
        """
        Initialize the chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk (default from settings)
            overlap_lines: Number of lines to overlap between chunks
        """
        self.max_tokens = max_tokens or settings.MAX_CHUNK_TOKENS
        self.overlap_lines = overlap_lines or settings.CHUNK_OVERLAP_LINES
    
    def chunk_file(
        self, 
        parsed_file: ParsedFile, 
        job_id: str
    ) -> List[Chunk]:
        """
        Split a parsed file into chunks.
        
        Args:
            parsed_file: ParsedFile object from parser
            job_id: Parent job identifier
            
        Returns:
            List of Chunk objects
        """
        if not parsed_file.content or not parsed_file.content.strip():
            logger.debug(f"Empty file, skipping: {parsed_file.file_path}")
            return []
        
        lines = parsed_file.content.split('\n')
        total_lines = len(lines)
        
        # If file is small enough, return as single chunk
        total_tokens = count_tokens_approximate(parsed_file.content)
        if total_tokens <= self.max_tokens:
            chunk = Chunk(
                chunk_id=self._generate_chunk_id(),
                job_id=job_id,
                file_path=parsed_file.file_path,
                language=parsed_file.language,
                start_line=1,
                end_line=total_lines,
                content=parsed_file.content,
                token_count=total_tokens
            )
            return [chunk]
        
        # Split into multiple chunks
        chunks = []
        current_start = 0
        
        while current_start < total_lines:
            # Find the end of this chunk
            chunk_end = self._find_chunk_end(
                lines, 
                current_start, 
                total_lines
            )
            
            # Extract chunk content
            chunk_lines = lines[current_start:chunk_end]
            chunk_content = '\n'.join(chunk_lines)
            
            # Ensure content ends with newline
            if chunk_content and not chunk_content.endswith('\n'):
                chunk_content += '\n'
            
            # Calculate token count
            token_count = count_tokens_approximate(chunk_content)
            
            # Create chunk
            chunk = Chunk(
                chunk_id=self._generate_chunk_id(),
                job_id=job_id,
                file_path=parsed_file.file_path,
                language=parsed_file.language,
                start_line=current_start + 1,  # 1-indexed
                end_line=chunk_end,            # 1-indexed (end is already correct)
                content=chunk_content,
                token_count=token_count
            )
            chunks.append(chunk)
            
            # Move to next chunk, accounting for overlap
            current_start = max(
                chunk_end - self.overlap_lines,
                chunk_end  # Don't go backwards
            )
            
            # Ensure we're making progress
            if current_start >= total_lines:
                break
            if chunk_end == current_start:
                current_start = chunk_end
        
        logger.debug(
            f"Chunked {parsed_file.file_path}: "
            f"{total_lines} lines -> {len(chunks)} chunks"
        )
        
        return chunks
    
    def _find_chunk_end(
        self, 
        lines: List[str], 
        start: int, 
        total_lines: int
    ) -> int:
        """
        Find the optimal end point for a chunk starting at 'start'.
        
        Tries to split at logical boundaries like:
        - Empty lines
        - End of functions/classes
        - End of blocks
        
        Args:
            lines: All lines in the file
            start: Starting line index (0-indexed)
            total_lines: Total number of lines
            
        Returns:
            End line index (exclusive, 0-indexed)
        """
        # Start with a maximum chunk size estimate
        # Estimate ~20 tokens per line as rough average for code
        estimated_lines_per_chunk = self.max_tokens // 20
        
        # Ensure minimum chunk size
        estimated_lines_per_chunk = max(estimated_lines_per_chunk, 10)
        
        # Calculate initial end point
        initial_end = min(start + estimated_lines_per_chunk, total_lines)
        
        # Accumulate lines and check token count
        current_end = start
        accumulated_content = []
        
        for i in range(start, total_lines):
            accumulated_content.append(lines[i])
            test_content = '\n'.join(accumulated_content)
            token_count = count_tokens_approximate(test_content)
            
            if token_count > self.max_tokens:
                # We've exceeded the limit, use previous position
                current_end = max(i, start + 1)  # At least one line
                break
            
            current_end = i + 1
        else:
            # Reached end of file
            current_end = total_lines
        
        # Try to find a better break point within the last portion
        if current_end > start + 1:
            better_end = self._find_logical_break(
                lines, 
                start, 
                current_end
            )
            if better_end > start:
                current_end = better_end
        
        return current_end
    
    def _find_logical_break(
        self, 
        lines: List[str], 
        start: int, 
        end: int
    ) -> int:
        """
        Find a logical break point within the given range.
        
        Prefers breaking at:
        1. Empty lines
        2. Lines that start new blocks (def, class, function, etc.)
        3. Lines with only closing braces/brackets
        
        Args:
            lines: All lines in the file
            start: Start index (0-indexed)
            end: End index (exclusive, 0-indexed)
            
        Returns:
            Better end index, or original end if no better point found
        """
        # Search backwards from end to find a good break point
        # Don't search too far back (at least 70% of the chunk should remain)
        min_end = start + int((end - start) * 0.7)
        
        # Patterns that indicate good break points
        break_patterns = [
            '',                    # Empty line
            '}',                   # Closing brace
            '};',                  # Closing brace with semicolon
            ']',                   # Closing bracket
            ')',                   # Closing paren (end of multi-line call)
        ]
        
        # Start patterns that indicate we should break BEFORE this line
        start_patterns = [
            'def ',
            'class ',
            'function ',
            'async def ',
            'async function ',
            'export ',
            'import ',
            'from ',
            '# ',                  # Comments
            '//',                  # Comments
            '/*',                  # Block comments
            '"""',                 # Docstrings
            "'''",                 # Docstrings
        ]
        
        best_break = end
        
        for i in range(end - 1, min_end - 1, -1):
            line = lines[i].strip()
            
            # Check for empty line (best break point)
            if not line:
                best_break = i + 1
                break
            
            # Check for closing patterns
            if line in break_patterns:
                best_break = i + 1
                break
            
            # Check if next line starts a new block
            if i + 1 < len(lines):
                next_line = lines[i + 1].lstrip()
                for pattern in start_patterns:
                    if next_line.startswith(pattern):
                        best_break = i + 1
                        break
        
        return best_break
    
    def _generate_chunk_id(self) -> str:
        """Generate a unique chunk identifier."""
        return f"chunk_{uuid.uuid4().hex[:16]}"


def chunk_parsed_file(
    parsed_file: ParsedFile, 
    job_id: str,
    max_tokens: Optional[int] = None
) -> List[Chunk]:
    """
    Convenience function to chunk a parsed file.
    
    Args:
        parsed_file: ParsedFile object
        job_id: Parent job identifier
        max_tokens: Optional max tokens override
        
    Returns:
        List of Chunk objects
    """
    chunker = TextChunker(max_tokens=max_tokens)
    return chunker.chunk_file(parsed_file, job_id)


def chunk_text(
    content: str,
    file_path: str,
    language: str,
    job_id: str,
    max_tokens: Optional[int] = None
) -> List[Chunk]:
    """
    Convenience function to chunk raw text content.
    
    Args:
        content: Text content to chunk
        file_path: File path for metadata
        language: Programming language
        job_id: Parent job identifier
        max_tokens: Optional max tokens override
        
    Returns:
        List of Chunk objects
    """
    # Create a ParsedFile object
    total_lines = content.count('\n') + 1 if content else 0
    
    parsed_file = ParsedFile(
        file_path=file_path,
        absolute_path=file_path,
        content=content,
        language=language,
        total_lines=total_lines,
        encoding='utf-8',
        size_bytes=len(content.encode('utf-8'))
    )
    
    return chunk_parsed_file(parsed_file, job_id, max_tokens)
