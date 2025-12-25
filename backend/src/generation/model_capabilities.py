"""
Model capabilities metadata for DocuMind AI.
Defines model-specific constraints and behaviors for adaptive prompt generation.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Literal
from enum import Enum

from src.utils.logger import get_logger

logger = get_logger("documind.model_capabilities")


class JSONSupport(str, Enum):
    """JSON output support levels."""
    NONE = "none"
    LIMITED = "limited"
    FULL = "full"


class CitationStrictness(str, Enum):
    """How strictly the model follows citation rules."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ModelCapabilities:
    """
    Capability metadata for an LLM model.
    Used to adapt prompts and generation parameters.
    """
    model_name: str
    max_context: int
    supports_tools: bool
    supports_json: JSONSupport
    supports_streaming: bool
    preferred_chunk_size: int
    citation_strictness: CitationStrictness
    default_temperature: float = 0.7
    requires_strict_prompts: bool = False
    thinking_model: bool = False  # Models that may output <think> tags
    
    @property
    def is_thinking_model(self) -> bool:
        """Property alias for thinking_model."""
        return self.thinking_model
    
    @property
    def recommended_temperature(self) -> float:
        """Property alias for default_temperature."""
        return self.default_temperature
    
    def get_effective_context(self, buffer: int = 500) -> int:
        """Get usable context size with safety buffer."""
        return max(self.max_context - buffer, 1000)
    
    def should_use_strict_rag(self) -> bool:
        """Determine if strict RAG prompts should be used."""
        return (
            self.requires_strict_prompts or
            self.citation_strictness == CitationStrictness.HIGH or
            self.max_context < 16000
        )


# =============================================================================
# Model Capability Registry
# =============================================================================

MODEL_CAPABILITIES: Dict[str, ModelCapabilities] = {
    # Local Ollama Models
    "qwen3:8b": ModelCapabilities(
        model_name="qwen3:8b",
        max_context=8192,
        supports_tools=False,
        supports_json=JSONSupport.LIMITED,
        supports_streaming=True,
        preferred_chunk_size=350,
        citation_strictness=CitationStrictness.HIGH,
        default_temperature=0.7,
        requires_strict_prompts=True,
        thinking_model=True
    ),
    "qwen2.5:7b": ModelCapabilities(
        model_name="qwen2.5:7b",
        max_context=32768,
        supports_tools=False,
        supports_json=JSONSupport.LIMITED,
        supports_streaming=True,
        preferred_chunk_size=500,
        citation_strictness=CitationStrictness.HIGH,
        default_temperature=0.7,
        requires_strict_prompts=True,
        thinking_model=False
    ),
    "llama3.1:8b": ModelCapabilities(
        model_name="llama3.1:8b",
        max_context=8192,
        supports_tools=False,
        supports_json=JSONSupport.LIMITED,
        supports_streaming=True,
        preferred_chunk_size=350,
        citation_strictness=CitationStrictness.MEDIUM,
        default_temperature=0.7,
        requires_strict_prompts=True,
        thinking_model=False
    ),
    "mistral:7b": ModelCapabilities(
        model_name="mistral:7b",
        max_context=8192,
        supports_tools=False,
        supports_json=JSONSupport.LIMITED,
        supports_streaming=True,
        preferred_chunk_size=350,
        citation_strictness=CitationStrictness.MEDIUM,
        default_temperature=0.7,
        requires_strict_prompts=True,
        thinking_model=False
    ),
    "codellama:7b": ModelCapabilities(
        model_name="codellama:7b",
        max_context=16384,
        supports_tools=False,
        supports_json=JSONSupport.NONE,
        supports_streaming=True,
        preferred_chunk_size=500,
        citation_strictness=CitationStrictness.LOW,
        default_temperature=0.5,
        requires_strict_prompts=True,
        thinking_model=False
    ),
    
    # Groq Models (Future)
    "llama-3.1-70b-versatile": ModelCapabilities(
        model_name="llama-3.1-70b-versatile",
        max_context=128000,
        supports_tools=True,
        supports_json=JSONSupport.FULL,
        supports_streaming=True,
        preferred_chunk_size=800,
        citation_strictness=CitationStrictness.MEDIUM,
        default_temperature=0.7,
        requires_strict_prompts=False,
        thinking_model=False
    ),
    "mixtral-8x7b-32768": ModelCapabilities(
        model_name="mixtral-8x7b-32768",
        max_context=32768,
        supports_tools=False,
        supports_json=JSONSupport.FULL,
        supports_streaming=True,
        preferred_chunk_size=600,
        citation_strictness=CitationStrictness.MEDIUM,
        default_temperature=0.7,
        requires_strict_prompts=False,
        thinking_model=False
    ),
    
    # OpenAI Models
    "gpt-3.5-turbo": ModelCapabilities(
        model_name="gpt-3.5-turbo",
        max_context=16385,
        supports_tools=True,
        supports_json=JSONSupport.FULL,
        supports_streaming=True,
        preferred_chunk_size=600,
        citation_strictness=CitationStrictness.MEDIUM,
        default_temperature=0.7,
        requires_strict_prompts=False,
        thinking_model=False
    ),
    "gpt-4o-mini": ModelCapabilities(
        model_name="gpt-4o-mini",
        max_context=128000,
        supports_tools=True,
        supports_json=JSONSupport.FULL,
        supports_streaming=True,
        preferred_chunk_size=800,
        citation_strictness=CitationStrictness.LOW,
        default_temperature=0.7,
        requires_strict_prompts=False,
        thinking_model=False
    ),
    
    # Hugging Face Models
    "mistralai/Mistral-7B-Instruct-v0.2": ModelCapabilities(
        model_name="mistralai/Mistral-7B-Instruct-v0.2",
        max_context=8192,
        supports_tools=False,
        supports_json=JSONSupport.LIMITED,
        supports_streaming=False,  # HF Inference API doesn't stream well
        preferred_chunk_size=350,
        citation_strictness=CitationStrictness.MEDIUM,
        default_temperature=0.7,
        requires_strict_prompts=True,
        thinking_model=False
    ),
    
    # Mock Model
    "mock-llm": ModelCapabilities(
        model_name="mock-llm",
        max_context=4096,
        supports_tools=False,
        supports_json=JSONSupport.NONE,
        supports_streaming=False,
        preferred_chunk_size=300,
        citation_strictness=CitationStrictness.HIGH,
        default_temperature=0.7,
        requires_strict_prompts=False,
        thinking_model=False
    ),
}

# Default capabilities for unknown models
DEFAULT_CAPABILITIES = ModelCapabilities(
    model_name="unknown",
    max_context=4096,
    supports_tools=False,
    supports_json=JSONSupport.LIMITED,
    supports_streaming=False,
    preferred_chunk_size=300,
    citation_strictness=CitationStrictness.HIGH,
    default_temperature=0.7,
    requires_strict_prompts=True,
    thinking_model=False
)


def get_model_capabilities(model_name: str) -> ModelCapabilities:
    """
    Get capabilities for a model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        ModelCapabilities for the model, or defaults if unknown
    """
    # Exact match
    if model_name in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model_name]
    
    # Partial match (for model variants like qwen3:8b-instruct)
    base_name = model_name.split(":")[0] if ":" in model_name else model_name
    for key, caps in MODEL_CAPABILITIES.items():
        if key.startswith(base_name) or base_name in key:
            logger.info(f"Using capabilities from '{key}' for model '{model_name}'")
            return caps
    
    logger.warning(f"Unknown model '{model_name}', using default capabilities")
    return DEFAULT_CAPABILITIES


def get_preferred_chunk_size(model_name: str) -> int:
    """Get the preferred chunk size for a model."""
    return get_model_capabilities(model_name).preferred_chunk_size


def supports_streaming(model_name: str) -> bool:
    """Check if a model supports streaming."""
    return get_model_capabilities(model_name).supports_streaming


def get_max_context(model_name: str) -> int:
    """Get the maximum context size for a model."""
    return get_model_capabilities(model_name).max_context
