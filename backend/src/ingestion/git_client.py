"""
Git client for cloning GitHub repositories.
Uses subprocess to execute git commands for reliability.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Tuple

from src.config import settings
from src.utils.logger import get_ingestion_logger
from src.utils.validators import sanitize_job_id

logger = get_ingestion_logger()


class GitClientError(Exception):
    """Custom exception for Git client errors."""
    pass


class GitClient:
    """
    Git client for cloning GitHub repositories.
    Clones repos to ./data/repos/<job_id>/ directory.
    """
    
    def __init__(self):
        """Initialize Git client and verify git is available."""
        self._verify_git_installed()
    
    def _verify_git_installed(self) -> None:
        """
        Verify that git is installed and available.
        
        Raises:
            GitClientError: If git is not installed
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise GitClientError("Git is not properly installed")
            
            logger.debug(f"Git version: {result.stdout.strip()}")
        except FileNotFoundError:
            raise GitClientError(
                "Git is not installed. Please install git to use this feature."
            )
        except subprocess.TimeoutExpired:
            raise GitClientError("Git command timed out")
    
    def clone_repository(
        self, 
        repo_url: str, 
        job_id: str,
        depth: int = 1
    ) -> Tuple[str, str]:
        """
        Clone a GitHub repository to local storage.
        
        Args:
            repo_url: GitHub repository URL
            job_id: Unique job identifier (used for directory name)
            depth: Clone depth (1 for shallow clone, 0 for full)
            
        Returns:
            Tuple of (local_path, repo_name)
            
        Raises:
            GitClientError: If cloning fails
        """
        # Sanitize job_id to prevent path traversal
        safe_job_id = sanitize_job_id(job_id)
        
        # Determine local clone path
        clone_path = settings.REPOS_DIR / safe_job_id
        
        # Check if path already exists
        if clone_path.exists():
            logger.warning(f"Directory already exists: {clone_path}")
            # Remove existing directory to ensure clean clone
            self._remove_directory(clone_path)
        
        # Create parent directory if needed
        clone_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build git clone command
        clone_cmd = ["git", "clone"]
        
        # Add depth for shallow clone (faster, less disk space)
        if depth > 0:
            clone_cmd.extend(["--depth", str(depth)])
        
        # Add single branch flag for efficiency
        clone_cmd.append("--single-branch")
        
        # Add repository URL and destination
        clone_cmd.extend([repo_url, str(clone_path)])
        
        logger.info(f"Cloning repository: {repo_url} -> {clone_path}")
        
        try:
            # Execute git clone
            result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}  # Disable prompts
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"Git clone failed: {error_msg}")
                
                # Provide user-friendly error messages
                if "Repository not found" in error_msg:
                    raise GitClientError(
                        f"Repository not found: {repo_url}. "
                        "Please verify the URL and ensure the repository is public."
                    )
                elif "Authentication failed" in error_msg:
                    raise GitClientError(
                        "Authentication failed. Only public repositories are supported."
                    )
                elif "already exists" in error_msg:
                    raise GitClientError(
                        f"Clone directory already exists: {clone_path}"
                    )
                else:
                    raise GitClientError(f"Git clone failed: {error_msg}")
            
            # Verify clone was successful
            if not clone_path.exists() or not (clone_path / ".git").exists():
                raise GitClientError("Clone appears to have failed - no .git directory found")
            
            # Extract repo name from path
            repo_name = clone_path.name
            
            logger.info(f"Successfully cloned repository to: {clone_path}")
            
            return str(clone_path), repo_name
            
        except subprocess.TimeoutExpired:
            # Clean up partial clone
            self._remove_directory(clone_path)
            raise GitClientError(
                f"Git clone timed out after 5 minutes. "
                "The repository may be too large or network is slow."
            )
        except subprocess.SubprocessError as e:
            # Clean up partial clone
            self._remove_directory(clone_path)
            raise GitClientError(f"Git clone failed: {str(e)}")
    
    def _remove_directory(self, path: Path) -> None:
        """
        Safely remove a directory and its contents.
        
        Args:
            path: Directory path to remove
        """
        if path.exists():
            try:
                shutil.rmtree(path)
                logger.debug(f"Removed directory: {path}")
            except Exception as e:
                logger.warning(f"Could not remove directory {path}: {e}")
    
    def get_repo_info(self, local_path: str) -> dict:
        """
        Get basic information about a cloned repository.
        
        Args:
            local_path: Path to the cloned repository
            
        Returns:
            Dictionary with repo information
        """
        info = {
            "path": local_path,
            "branch": None,
            "commit": None,
            "remote_url": None
        }
        
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=local_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                info["branch"] = result.stdout.strip()
            
            # Get current commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=local_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                info["commit"] = result.stdout.strip()
            
            # Get remote URL
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=local_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                info["remote_url"] = result.stdout.strip()
                
        except Exception as e:
            logger.warning(f"Could not get repo info: {e}")
        
        return info
    
    def cleanup_repository(self, job_id: str) -> bool:
        """
        Remove a cloned repository.
        
        Args:
            job_id: Job identifier (directory name)
            
        Returns:
            True if removed successfully, False otherwise
        """
        safe_job_id = sanitize_job_id(job_id)
        repo_path = settings.REPOS_DIR / safe_job_id
        
        if repo_path.exists():
            self._remove_directory(repo_path)
            logger.info(f"Cleaned up repository: {repo_path}")
            return True
        
        return False


# Module-level convenience function
def clone_repo(repo_url: str, job_id: str) -> Tuple[str, str]:
    """
    Convenience function to clone a repository.
    
    Args:
        repo_url: GitHub repository URL
        job_id: Unique job identifier
        
    Returns:
        Tuple of (local_path, repo_name)
    """
    client = GitClient()
    return client.clone_repository(repo_url, job_id)
