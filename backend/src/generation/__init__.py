"""
Generation module for DocuMind AI.
Implements RAG (Retrieval-Augmented Generation) for code documentation.

This module provides:
- LLM client integrations (HuggingFace, OpenAI-compatible)
- Prompt templates with anti-hallucination rules
- RAG generator orchestration
"""

from src.generation.llm_client import (
    BaseLLMClient,
    LLMResponse,
    LLMClientError,
    LLMProvider,
    MockLLMClient,
    HuggingFaceLLMClient,
    OpenAICompatibleClient,
    get_llm_client,
    get_default_llm_client
)

from src.generation.templates import (
    PromptBuilder,
    CodeSnippet,
    get_prompt_builder,
    get_default_prompt_builder,
    create_snippet_from_retrieval,
    SYSTEM_PROMPT_CODE_ASSISTANT,
    SYSTEM_PROMPT_MINIMAL
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
    "OpenAICompatibleClient",
    "get_llm_client",
    "get_default_llm_client",
    # Templates
    "PromptBuilder",
    "CodeSnippet",
    "get_prompt_builder",
    "get_default_prompt_builder",
    "create_snippet_from_retrieval",
    "SYSTEM_PROMPT_CODE_ASSISTANT",
    "SYSTEM_PROMPT_MINIMAL",
    # Generator
    "Generator",
    "GeneratorError",
    "GenerationResponse",
    "GenerationStatus",
    "SourceReference",
    "get_generator",
    "generate_answer"
]
