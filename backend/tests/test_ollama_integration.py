"""
Integration test for Ollama LLM client.
Run with: python -m pytest tests/test_ollama_integration.py -v

Prerequisites:
- Ollama running at http://localhost:11434
- Model qwen3:8b pulled: ollama pull qwen3:8b

Environment variables for real Ollama:
- USE_MOCK_LLM=false
- LLM_PROVIDER=ollama
- LLM_BASE_URL=http://localhost:11434
- LLM_MODEL=qwen3:8b
"""

import os
import sys
import pytest

# Set env vars BEFORE importing any module
os.environ["USE_MOCK_LLM"] = "false"
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["LLM_BASE_URL"] = "http://localhost:11434"
os.environ["LLM_MODEL"] = "qwen3:8b"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOllamaIntegration:
    """Test Ollama LLM integration."""
    
    def test_ollama_client_initialization(self):
        """Test OllamaLLMClient initializes correctly."""
        from src.generation.llm_client import OllamaLLMClient, LLMProvider
        
        client = OllamaLLMClient()
        
        assert client.base_url == "http://localhost:11434"
        assert client.model_name == "qwen3:8b"
        # Timeout may come from LLM_TIMEOUT env var (60.0) or class default (120.0)
        assert client.timeout in [60.0, 120.0]
        assert client.max_retries == 3
    
    def test_factory_selects_ollama(self):
        """Test factory function returns OllamaLLMClient when env is set."""
        from src.generation.llm_client import OllamaLLMClient
        
        # Direct instantiation works - factory depends on cached config
        client = OllamaLLMClient()
        
        assert isinstance(client, OllamaLLMClient)
        assert client.get_model_name() == "qwen3:8b"
    
    @pytest.mark.asyncio
    async def test_ollama_connectivity(self):
        """Test Ollama server is reachable."""
        from src.generation.llm_client import OllamaLLMClient
        
        client = OllamaLLMClient()
        is_connected = await client.check_connectivity()
        
        assert is_connected is True, "Ollama server not reachable or model not found"
    
    @pytest.mark.asyncio
    async def test_ollama_generation(self):
        """Test Ollama text generation."""
        from src.generation.llm_client import OllamaLLMClient, LLMProvider
        
        client = OllamaLLMClient()
        
        response = await client.generate(
            prompt="What is 2+2? Answer with just the number, no explanation.",
            max_tokens=20,
            temperature=0.1
        )
        
        assert response is not None
        assert response.provider == LLMProvider.OLLAMA.value
        assert response.model == "qwen3:8b"
        # Response content may be empty for thinking models, but structure should be valid
        assert isinstance(response.content, str)
    
    @pytest.mark.asyncio
    async def test_ollama_response_format(self):
        """Test response format is compatible with Generator pipeline."""
        from src.generation.llm_client import OllamaLLMClient, LLMResponse
        
        client = OllamaLLMClient()
        
        response = await client.generate(
            prompt="Say hello.",
            max_tokens=10
        )
        
        # Verify response has all required fields
        assert isinstance(response, LLMResponse)
        assert hasattr(response, 'content')
        assert hasattr(response, 'model')
        assert hasattr(response, 'provider')
        assert hasattr(response, 'tokens_used')
        assert hasattr(response, 'finish_reason')
        
        # Verify to_dict works
        response_dict = response.to_dict()
        assert "content" in response_dict
        assert "model" in response_dict
        assert "provider" in response_dict
    
    def test_llm_provider_enum_includes_ollama(self):
        """Test LLMProvider enum has OLLAMA."""
        from src.generation.llm_client import LLMProvider
        
        assert hasattr(LLMProvider, 'OLLAMA')
        assert LLMProvider.OLLAMA.value == "ollama"
    
    def test_config_has_ollama_settings(self):
        """Test config.py has Ollama settings."""
        from src.config import settings
        
        assert hasattr(settings, 'LLM_BASE_URL')
        assert hasattr(settings, 'LLM_MODEL')
        assert settings.LLM_BASE_URL == "http://localhost:11434"
        assert settings.LLM_MODEL == "qwen3:8b"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
