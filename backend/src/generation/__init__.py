"""
Generation module for DocuMind AI.
Implements RAG (Retrieval-Augmented Generation) for code documentation.

This module provides:
- LLM client integrations (Ollama, HuggingFace, OpenAI-compatible)
- Prompt templates with anti-hallucination rules
- RAG generator orchestration
- Model capability metadata for adaptive prompts
"""

from src.generation.llm_client import (
    BaseLLMClient,
    LLMResponse,
    LLMClientError,
    LLMProvider,
    MockLLMClient,
    HuggingFaceLLMClient,
    OllamaLLMClient,
    OpenAICompatibleClient,
    get_llm_client,
    get_default_llm_client
)

from src.generation.templates import (
    PromptBuilder,
    AdaptivePromptBuilder,
    CodeSnippet,
    get_prompt_builder,
    get_default_prompt_builder,
    get_strict_rag_builder,
    get_streaming_builder,
    create_snippet_from_retrieval,
    SYSTEM_PROMPT_MASTER,
    SYSTEM_PROMPT_CODE_ASSISTANT,
    SYSTEM_PROMPT_MINIMAL,
    SYSTEM_PROMPT_STRICT_RAG,
    SYSTEM_PROMPT_STREAMING,
    SYSTEM_PROMPT_UNIVERSAL,
    MASTER_RAG_CONTEXT_TEMPLATE,
    MASTER_RAG_SNIPPET_TEMPLATE
)

from src.generation.model_capabilities import (
    ModelCapabilities,
    JSONSupport,
    CitationStrictness,
    MODEL_CAPABILITIES,
    get_model_capabilities,
    get_preferred_chunk_size,
    supports_streaming,
    get_max_context
)

from src.generation.generator import (
    Generator,
    GeneratorError,
    GenerationResponse,
    GenerationStatus,
    SourceReference,
    get_generator,
    generate_answer
)

__all__ = [
    # LLM Client
    "BaseLLMClient",
    "LLMResponse",
    "LLMClientError",
    "LLMProvider",
    "MockLLMClient",
    "HuggingFaceLLMClient",
    "OllamaLLMClient",
    "OpenAICompatibleClient",
    "get_llm_client",
    "get_default_llm_client",
    # Templates
    "PromptBuilder",
    "AdaptivePromptBuilder",
    "CodeSnippet",
    "get_prompt_builder",
    "get_default_prompt_builder",
    "get_strict_rag_builder",
    "get_streaming_builder",
    "create_snippet_from_retrieval",
    "SYSTEM_PROMPT_MASTER",
    "SYSTEM_PROMPT_CODE_ASSISTANT",
    "SYSTEM_PROMPT_MINIMAL",
    "SYSTEM_PROMPT_STRICT_RAG",
    "SYSTEM_PROMPT_STREAMING",
    "SYSTEM_PROMPT_UNIVERSAL",
    "MASTER_RAG_CONTEXT_TEMPLATE",
    "MASTER_RAG_SNIPPET_TEMPLATE",
    # Model Capabilities
    "ModelCapabilities",
    "JSONSupport",
    "CitationStrictness",
    "MODEL_CAPABILITIES",
    "get_model_capabilities",
    "get_preferred_chunk_size",
    "supports_streaming",
    "get_max_context",
    # Generator
    "Generator",
    "GeneratorError",
    "GenerationResponse",
    "GenerationStatus",
    "SourceReference",
    "get_generator",
    "generate_answer"
]
