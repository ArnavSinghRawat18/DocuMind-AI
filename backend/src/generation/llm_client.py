"""
LLM Client module for DocuMind AI.
Provides a pluggable interface for Language Model integrations.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("documind.llm_client")


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    MOCK = "mock"


@dataclass
class LLMResponse:
    """Represents a response from an LLM."""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "tokens_used": self.tokens_used,
            "finish_reason": self.finish_reason
        }


class LLMClientError(Exception):
    """Custom exception for LLM client operations."""
    pass


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse object
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the current model name."""
        pass


class MockLLMClient(BaseLLMClient):
    """
    Mock LLM client for testing purposes.
    Returns predefined responses without making external API calls.
    """
    
    def __init__(self, model_name: str = "mock-llm"):
        self.model_name = model_name
        logger.info(f"Initialized MockLLMClient with model: {model_name}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a mock response."""
        # Simulate some processing delay
        await asyncio.sleep(0.1)
        
        # Generate a simple mock response based on prompt content
        mock_content = self._generate_mock_content(prompt)
        
        return LLMResponse(
            content=mock_content,
            model=self.model_name,
            provider=LLMProvider.MOCK.value,
            tokens_used=len(mock_content.split()),
            finish_reason="stop"
        )
    
    def _generate_mock_content(self, prompt: str) -> str:
        """Generate mock content based on prompt."""
        # Extract query if present in prompt
        if "Question:" in prompt or "Query:" in prompt:
            return (
                "Based on the code context provided, here is my analysis:\n\n"
                "The code appears to implement a specific functionality. "
                "Key points:\n"
                "1. The implementation follows standard patterns\n"
                "2. Error handling is present\n"
                "3. The code is well-structured\n\n"
                "**Note:** This is a mock response for testing purposes."
            )
        return "Mock LLM response for testing. No specific query detected."
    
    def get_model_name(self) -> str:
        return self.model_name


class HuggingFaceLLMClient(BaseLLMClient):
    """
    Hugging Face Inference API client.
    Uses HTTP requests to interact with HF models.
    """
    
    # Default models for different use cases
    DEFAULT_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        """
        Initialize the Hugging Face LLM client.
        
        Args:
            api_key: HF API key (defaults to env var)
            model_name: Model to use (defaults to HF_LLM_MODEL env var)
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts
        """
        self.api_key = api_key or os.getenv("HF_API_KEY", settings.HF_API_KEY)
        self.model_name = model_name or os.getenv("HF_LLM_MODEL", self.DEFAULT_MODEL)
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = "https://api-inference.huggingface.co/models"
        
        if not self.api_key:
            logger.warning("No HF_API_KEY provided, HuggingFace client may fail")
        
        logger.info(f"Initialized HuggingFaceLLMClient with model: {self.model_name}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using Hugging Face Inference API.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum new tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse object
            
        Raises:
            LLMClientError: If generation fails after retries
        """
        # Import httpx lazily to avoid startup overhead
        try:
            import httpx
        except ImportError:
            raise LLMClientError(
                "httpx not installed. Install with: pip install httpx"
            )
        
        url = f"{self.base_url}/{self.model_name}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "do_sample": temperature > 0,
                "return_full_text": False,
                **kwargs
            }
        }
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        result = response.json()
                        return self._parse_response(result)
                    
                    elif response.status_code == 503:
                        # Model loading - wait and retry
                        error_data = response.json()
                        wait_time = error_data.get("estimated_time", 20)
                        logger.warning(
                            f"Model loading, waiting {wait_time}s (attempt {attempt + 1})"
                        )
                        await asyncio.sleep(min(wait_time, 30))
                        continue
                    
                    elif response.status_code == 429:
                        # Rate limited - exponential backoff
                        wait_time = (2 ** attempt) + 1
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        error_text = response.text
                        logger.error(f"HF API error {response.status_code}: {error_text}")
                        raise LLMClientError(
                            f"HF API error: {response.status_code} - {error_text}"
                        )
                        
            except httpx.TimeoutException:
                last_error = LLMClientError(f"Request timeout after {self.timeout}s")
                logger.warning(f"Timeout on attempt {attempt + 1}")
                await asyncio.sleep(2 ** attempt)
                
            except httpx.RequestError as e:
                last_error = LLMClientError(f"Request error: {str(e)}")
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                await asyncio.sleep(2 ** attempt)
        
        raise last_error or LLMClientError("Failed after all retries")
    
    def _parse_response(self, result: Any) -> LLMResponse:
        """Parse the HF API response."""
        if isinstance(result, list) and len(result) > 0:
            content = result[0].get("generated_text", "")
        elif isinstance(result, dict):
            content = result.get("generated_text", str(result))
        else:
            content = str(result)
        
        return LLMResponse(
            content=content.strip(),
            model=self.model_name,
            provider=LLMProvider.HUGGINGFACE.value,
            tokens_used=None,  # HF doesn't always return token count
            finish_reason="stop",
            raw_response=result if isinstance(result, dict) else {"result": result}
        )
    
    def get_model_name(self) -> str:
        return self.model_name


class OpenAICompatibleClient(BaseLLMClient):
    """
    OpenAI-compatible client for any API following the OpenAI format.
    Can be used with OpenAI, Azure OpenAI, or local servers like Ollama.
    """
    
    DEFAULT_MODEL = "gpt-3.5-turbo"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        """
        Initialize the OpenAI-compatible client.
        
        Args:
            api_key: API key (defaults to OPENAI_API_KEY env var)
            model_name: Model name to use
            base_url: API base URL (defaults to OpenAI)
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", settings.OPENAI_API_KEY)
        self.model_name = model_name or os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL)
        self.base_url = base_url or os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            logger.warning("No OPENAI_API_KEY provided")
        
        logger.info(f"Initialized OpenAICompatibleClient with model: {self.model_name}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using OpenAI-compatible API.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters (system_prompt, etc.)
            
        Returns:
            LLMResponse object
        """
        try:
            import httpx
        except ImportError:
            raise LLMClientError(
                "httpx not installed. Install with: pip install httpx"
            )
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build messages
        messages = []
        if "system_prompt" in kwargs:
            messages.append({"role": "system", "content": kwargs.pop("system_prompt")})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **{k: v for k, v in kwargs.items() if k not in ["system_prompt"]}
        }
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        result = response.json()
                        return self._parse_response(result)
                    
                    elif response.status_code == 429:
                        wait_time = (2 ** attempt) + 1
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        error_text = response.text
                        logger.error(f"OpenAI API error {response.status_code}: {error_text}")
                        raise LLMClientError(
                            f"OpenAI API error: {response.status_code} - {error_text}"
                        )
                        
            except httpx.TimeoutException:
                last_error = LLMClientError(f"Request timeout after {self.timeout}s")
                logger.warning(f"Timeout on attempt {attempt + 1}")
                await asyncio.sleep(2 ** attempt)
                
            except httpx.RequestError as e:
                last_error = LLMClientError(f"Request error: {str(e)}")
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                await asyncio.sleep(2 ** attempt)
        
        raise last_error or LLMClientError("Failed after all retries")
    
    def _parse_response(self, result: Dict[str, Any]) -> LLMResponse:
        """Parse the OpenAI API response."""
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        
        usage = result.get("usage", {})
        total_tokens = usage.get("total_tokens")
        
        return LLMResponse(
            content=content.strip(),
            model=result.get("model", self.model_name),
            provider="openai",
            tokens_used=total_tokens,
            finish_reason=choice.get("finish_reason"),
            raw_response=result
        )
    
    def get_model_name(self) -> str:
        return self.model_name


# =============================================================================
# Factory function for creating LLM clients
# =============================================================================

def get_llm_client(
    provider: Optional[str] = None,
    **kwargs
) -> BaseLLMClient:
    """
    Factory function to get an LLM client instance.
    
    Args:
        provider: LLM provider name ("huggingface", "openai", "mock")
                  Defaults to env var LLM_PROVIDER or "mock"
        **kwargs: Additional arguments for the client constructor
        
    Returns:
        Configured LLM client instance
    """
    # Determine provider
    provider = provider or os.getenv("LLM_PROVIDER", "mock")
    provider = provider.lower()
    
    # Check for mock mode
    use_mock = os.getenv("USE_MOCK_LLM", "true").lower() == "true"
    
    if use_mock or provider == "mock":
        logger.info("Using MockLLMClient")
        return MockLLMClient(**kwargs)
    
    if provider == "huggingface" or provider == "hf":
        return HuggingFaceLLMClient(**kwargs)
    
    if provider == "openai":
        return OpenAICompatibleClient(**kwargs)
    
    # Default to mock for safety
    logger.warning(f"Unknown provider '{provider}', falling back to mock")
    return MockLLMClient(**kwargs)


# Singleton instance for convenience
_llm_client: Optional[BaseLLMClient] = None


def get_default_llm_client() -> BaseLLMClient:
    """Get or create the default LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = get_llm_client()
    return _llm_client
