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
    OLLAMA = "ollama"
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
    
    def supports_streaming(self) -> bool:
        """Check if this client supports streaming. Override in subclasses."""
        return False


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


class OllamaLLMClient(BaseLLMClient):
    """
    Ollama LLM client for local model inference.
    Communicates with Ollama server via HTTP API.
    No API key required - runs locally.
    """
    
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "qwen3:8b"
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 3
    ):
        """
        Initialize the Ollama LLM client.
        
        Args:
            base_url: Ollama server URL (defaults to LLM_BASE_URL env var)
            model_name: Model to use (defaults to LLM_MODEL env var)
            timeout: Request timeout in seconds (longer for local inference)
            max_retries: Number of retry attempts
        """
        self.base_url = base_url or os.getenv("LLM_BASE_URL", self.DEFAULT_BASE_URL)
        self.model_name = model_name or os.getenv("LLM_MODEL", self.DEFAULT_MODEL)
        self.timeout = float(os.getenv("LLM_TIMEOUT", str(timeout)))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", str(max_retries)))
        
        # Remove trailing slash if present
        self.base_url = self.base_url.rstrip("/")
        
        logger.info(f"Initialized OllamaLLMClient: {self.base_url} with model: {self.model_name}")
    
    async def check_connectivity(self) -> bool:
        """
        Check if Ollama server is reachable and model is available.
        
        Returns:
            True if connected and model exists, False otherwise
        """
        try:
            import httpx
        except ImportError:
            logger.error("httpx not installed")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check server is running
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    logger.error(f"Ollama server not responding: {response.status_code}")
                    return False
                
                # Check if model exists
                models_data = response.json()
                models = [m.get("name", "") for m in models_data.get("models", [])]
                
                # Match model name (with or without :latest tag)
                model_found = any(
                    self.model_name in m or m.startswith(self.model_name.split(":")[0])
                    for m in models
                )
                
                if not model_found:
                    logger.warning(f"Model '{self.model_name}' not found. Available: {models}")
                    return False
                
                logger.info(f"Ollama connectivity verified. Model '{self.model_name}' available.")
                return True
                
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}")
            return False
        except Exception as e:
            logger.error(f"Ollama connectivity check failed: {e}")
            return False
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using Ollama's generate API.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate (num_predict)
            temperature: Sampling temperature
            **kwargs: Additional Ollama parameters
            
        Returns:
            LLMResponse object
            
        Raises:
            LLMClientError: If generation fails after retries
        """
        try:
            import httpx
        except ImportError:
            raise LLMClientError(
                "httpx not installed. Install with: pip install httpx"
            )
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                **kwargs
            }
        }
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        return self._parse_response(result)
                    
                    elif response.status_code == 404:
                        raise LLMClientError(
                            f"Model '{self.model_name}' not found. Pull it with: ollama pull {self.model_name}"
                        )
                    
                    else:
                        error_text = response.text
                        logger.error(f"Ollama API error {response.status_code}: {error_text}")
                        raise LLMClientError(
                            f"Ollama error: {response.status_code} - {error_text}"
                        )
                        
            except httpx.ConnectError:
                last_error = LLMClientError(
                    f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?"
                )
                logger.warning(f"Connection failed on attempt {attempt + 1}")
                await asyncio.sleep(2 ** attempt)
                
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
        """Parse the Ollama API response."""
        content = result.get("response", "")
        
        # Ollama provides token counts
        prompt_tokens = result.get("prompt_eval_count", 0)
        completion_tokens = result.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens
        
        return LLMResponse(
            content=content.strip(),
            model=result.get("model", self.model_name),
            provider=LLMProvider.OLLAMA.value,
            tokens_used=total_tokens if total_tokens > 0 else None,
            finish_reason="stop" if result.get("done", False) else "length",
            raw_response=result
        )
    
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Generate a streaming response using Ollama's generate API.
        
        Yields tokens as they are generated for real-time UI updates.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate (num_predict)
            temperature: Sampling temperature
            **kwargs: Additional Ollama parameters
            
        Yields:
            str: Individual tokens/chunks as they are generated
            
        Raises:
            LLMClientError: If generation fails
        """
        try:
            import httpx
        except ImportError:
            raise LLMClientError(
                "httpx not installed. Install with: pip install httpx"
            )
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,  # Enable streaming
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                **kwargs
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise LLMClientError(
                            f"Ollama error: {response.status_code} - {error_text.decode()}"
                        )
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        try:
                            import json
                            chunk = json.loads(line)
                            
                            # Yield the response token
                            token = chunk.get("response", "")
                            if token:
                                yield token
                            
                            # Check if done
                            if chunk.get("done", False):
                                break
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse streaming chunk: {line}")
                            continue
                            
        except httpx.ConnectError:
            raise LLMClientError(
                f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?"
            )
        except httpx.TimeoutException:
            raise LLMClientError(f"Streaming timeout after {self.timeout}s")
        except httpx.RequestError as e:
            raise LLMClientError(f"Streaming request error: {str(e)}")
    
    def supports_streaming(self) -> bool:
        """Check if this client supports streaming."""
        return True
    
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
        provider: LLM provider name ("ollama", "huggingface", "openai", "mock")
                  Defaults to settings.LLM_PROVIDER or "mock"
        **kwargs: Additional arguments for the client constructor
        
    Returns:
        Configured LLM client instance
    """
    from src.config import settings
    
    # Determine provider from settings
    provider = provider or settings.LLM_PROVIDER or "mock"
    provider = provider.lower()
    
    # Check for mock mode from settings
    use_mock = settings.USE_MOCK_LLM
    
    logger.info(f"get_llm_client: provider={provider}, USE_MOCK_LLM={use_mock}")
    
    if use_mock or provider == "mock":
        logger.info("Using MockLLMClient")
        return MockLLMClient(**kwargs)
    
    if provider == "ollama":
        logger.info(f"Using OllamaLLMClient (model={settings.LLM_MODEL})")
        return OllamaLLMClient(
            base_url=settings.LLM_BASE_URL,
            model_name=settings.LLM_MODEL,
            **kwargs
        )
    
    if provider == "huggingface" or provider == "hf":
        logger.info("Using HuggingFaceLLMClient")
        return HuggingFaceLLMClient(**kwargs)
    
    if provider == "openai":
        logger.info("Using OpenAICompatibleClient")
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
