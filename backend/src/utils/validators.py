"""
Input validation utilities for DocuMind AI backend.
Provides validation functions for GitHub URLs and other inputs.
"""

import re
from typing import Tuple, Optional, Set
from urllib.parse import urlparse

from src.config import settings


# Regex pattern for valid GitHub repository URLs
GITHUB_URL_PATTERNS = [
    # HTTPS format: https://github.com/owner/repo or https://github.com/owner/repo.git
    r'^https?://github\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?/?$',
    # SSH format: git@github.com:owner/repo.git
    r'^git@github\.com:[\w\-\.]+/[\w\-\.]+\.git$',
]

# Generic Git URL patterns (for other hosts)
GENERIC_GIT_URL_PATTERNS = [
    r'^https?://[\w\-\.]+/[\w\-\.]+/[\w\-\.]+(?:\.git)?/?$',
    r'^git@[\w\-\.]+:[\w\-\.]+/[\w\-\.]+\.git$',
]


def validate_github_url(url: str) -> Tuple[bool, str]:
    """
    Validate a GitHub repository URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is empty string
    """
    if not url:
        return False, "Repository URL is required"
    
    url = url.strip()
    
    # Length check
    if len(url) > settings.MAX_REPO_URL_LENGTH:
        return False, f"URL too long (max {settings.MAX_REPO_URL_LENGTH} characters)"
    
    # Check against known patterns
    for pattern in GITHUB_URL_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            return True, ""
    
    # Provide specific error messages
    parsed = urlparse(url)
    
    if not parsed.scheme:
        return False, "Invalid URL format: missing protocol (https://)"
    
    if parsed.netloc not in ['github.com', 'www.github.com']:
        return False, f"Only GitHub repositories are supported. Got: {parsed.netloc}"
    
    if not parsed.path or parsed.path == '/':
        return False, "Invalid GitHub URL: missing owner/repository path"
    
    # Check path format (should be /owner/repo)
    path_parts = [p for p in parsed.path.strip('/').split('/') if p]
    if len(path_parts) < 2:
        return False, "Invalid GitHub URL: should be in format github.com/owner/repo"
    
    return False, "Invalid GitHub URL format"


def validate_git_url(url: str, allowed_hosts: Optional[Set[str]] = None) -> Tuple[bool, str]:
    """
    Validate a Git repository URL against allowed hosts.
    
    Args:
        url: The URL to validate
        allowed_hosts: Set of allowed hostnames (defaults to config.ALLOWED_GIT_HOSTS)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "Repository URL is required"
    
    url = url.strip()
    allowed_hosts = allowed_hosts or settings.ALLOWED_GIT_HOSTS
    
    # Length check
    if len(url) > settings.MAX_REPO_URL_LENGTH:
        return False, f"URL too long (max {settings.MAX_REPO_URL_LENGTH} characters)"
    
    # Parse URL to get hostname
    if url.startswith('git@'):
        # SSH format: git@hostname:path
        match = re.match(r'^git@([\w\-\.]+):', url)
        if match:
            hostname = match.group(1)
        else:
            return False, "Invalid SSH URL format"
    else:
        parsed = urlparse(url)
        hostname = parsed.netloc
    
    # Check hostname against allowed list
    if hostname not in allowed_hosts:
        return False, f"Git host not allowed: {hostname}. Allowed: {', '.join(allowed_hosts)}"
    
    # Validate URL structure
    for pattern in GITHUB_URL_PATTERNS + GENERIC_GIT_URL_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            return True, ""
    
    return False, "Invalid Git URL format"


def extract_repo_info(url: str) -> Tuple[str, str]:
    """
    Extract owner and repository name from a GitHub URL.
    
    Args:
        url: Valid GitHub repository URL
        
    Returns:
        Tuple of (owner, repo_name)
        
    Raises:
        ValueError: If URL is invalid
    """
    url = url.strip()
    
    # Handle SSH format
    if url.startswith('git@github.com:'):
        path = url.replace('git@github.com:', '').replace('.git', '')
        parts = path.split('/')
        if len(parts) >= 2:
            return parts[0], parts[1]
    
    # Handle HTTPS format
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.strip('/').split('/') if p]
    
    if len(path_parts) >= 2:
        repo_name = path_parts[1].replace('.git', '')
        return path_parts[0], repo_name
    
    raise ValueError(f"Could not extract owner/repo from URL: {url}")


def sanitize_job_id(job_id: str) -> str:
    """
    Sanitize a job ID to prevent path traversal attacks.
    
    Args:
        job_id: The job ID to sanitize
        
    Returns:
        Sanitized job ID
        
    Raises:
        ValueError: If job ID contains invalid characters
    """
    if not job_id:
        raise ValueError("Job ID cannot be empty")
    
    # Only allow alphanumeric characters, hyphens, and underscores
    if not re.match(r'^[\w\-]+$', job_id):
        raise ValueError("Job ID contains invalid characters")
    
    return job_id


def validate_file_path(path: str, allowed_extensions: set) -> bool:
    """
    Validate if a file path has an allowed extension.
    
    Args:
        path: File path to validate
        allowed_extensions: Set of allowed file extensions (e.g., {'.py', '.js'})
        
    Returns:
        True if file has allowed extension, False otherwise
    """
    if not path:
        return False
    
    # Get file extension (lowercase)
    ext = '.' + path.rsplit('.', 1)[-1].lower() if '.' in path else ''
    
    return ext in allowed_extensions


def validate_query(query: str, max_length: Optional[int] = None) -> Tuple[bool, str]:
    """
    Validate a search/generation query.
    
    Args:
        query: The query string to validate
        max_length: Maximum allowed length (defaults to config.MAX_QUERY_LENGTH)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query:
        return False, "Query cannot be empty"
    
    query = query.strip()
    max_length = max_length or settings.MAX_QUERY_LENGTH
    
    if not query:
        return False, "Query cannot be empty or whitespace only"
    
    if len(query) > max_length:
        return False, f"Query too long (max {max_length} characters)"
    
    # Check for potentially malicious patterns
    suspicious_patterns = [
        r'<script[^>]*>',  # Script tags
        r'javascript:',     # JavaScript protocol
        r'on\w+\s*=',       # Event handlers
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False, "Query contains potentially unsafe content"
    
    return True, ""


def sanitize_query(query: str) -> str:
    """
    Sanitize a query string by removing potentially dangerous content.
    
    Args:
        query: The query string to sanitize
        
    Returns:
        Sanitized query string
    """
    if not query:
        return ""
    
    # Strip whitespace
    query = query.strip()
    
    # Remove null bytes
    query = query.replace('\x00', '')
    
    # Limit to max length
    query = query[:settings.MAX_QUERY_LENGTH]
    
    return query


def validate_uuid(value: str) -> bool:
    """
    Validate if a string is a valid UUID format.
    
    Args:
        value: String to validate
        
    Returns:
        True if valid UUID format, False otherwise
    """
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, value, re.IGNORECASE))
