"""
Generator module for DocuMind AI.
Orchestrates RAG (Retrieval-Augmented Generation) pipeline.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from enum import Enum

from src.config import settings
from src.retrieval.retriever import Retriever, RetrievalResult, RetrieverError, get_retriever
from src.generation.llm_client import (
    BaseLLMClient,
    LLMResponse,
    LLMClientError,
    get_default_llm_client
)
from src.generation.templates import (
    PromptBuilder,
    CodeSnippet,
    get_default_prompt_builder
)
from src.utils.logger import get_logger

logger = get_logger("documind.generator")


class GenerationStatus(str, Enum):
    """Status codes for generation responses."""
    SUCCESS = "success"
    PARTIAL = "partial"  # Generated but with limited context
    NO_CONTEXT = "no_context"  # No relevant code found
    ERROR = "error"


@dataclass
class SourceReference:
    """Reference to a source code snippet used in generation."""
    file_path: str
    start_line: int
    end_line: int
    language: str
    relevance_score: float
    snippet_preview: str  # First 200 chars of content
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GenerationResponse:
    """Complete response from the generation pipeline."""
    answer: str
    status: GenerationStatus
    sources: List[SourceReference]
    confidence: float  # 0.0 - 1.0 based on context quality
    model: str
    job_id: str
    query: str
    tokens_used: Optional[int] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "status": self.status.value,
            "sources": [s.to_dict() for s in self.sources],
            "confidence": self.confidence,
            "model": self.model,
            "job_id": self.job_id,
            "query": self.query,
            "tokens_used": self.tokens_used,
            "error_message": self.error_message
        }


class GeneratorError(Exception):
    """Custom exception for generator operations."""
    pass


class Generator:
    """
    RAG Generator for code documentation.
    
    Orchestrates the complete RAG pipeline:
    1. Retrieve relevant code chunks
    2. Build context-aware prompts
    3. Generate responses using LLM
    4. Structure and return results
    """
    
    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        llm_client: Optional[BaseLLMClient] = None,
        prompt_builder: Optional[PromptBuilder] = None
    ):
        """
        Initialize the generator.
        
        Args:
            retriever: Retriever instance for code search
            llm_client: LLM client for generation
            prompt_builder: Prompt builder for formatting
        """
        self._retriever = retriever or get_retriever()
        self._llm_client = llm_client or get_default_llm_client()
        self._prompt_builder = prompt_builder or get_default_prompt_builder()
        
        logger.info(
            f"Initialized Generator with model: {self._llm_client.get_model_name()}"
        )
    
    async def generate(
        self,
        query: str,
        job_id: str,
        top_k: int = 5,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        score_threshold: Optional[float] = None
    ) -> GenerationResponse:
        """
        Generate a response for a query about a codebase.
        
        Args:
            query: The user's question
            job_id: Job ID to search within
            top_k: Number of code chunks to retrieve
            max_tokens: Maximum tokens in response
            temperature: LLM sampling temperature
            score_threshold: Minimum relevance score for chunks
            
        Returns:
            GenerationResponse with answer, sources, and metadata
            
        Raises:
            GeneratorError: If generation fails
        """
        logger.info(f"Generating response for query in job {job_id}")
        
        # Step 1: Retrieve relevant code chunks
        try:
            retrieval_results = await self._retriever.retrieve(
                query=query,
                job_id=job_id,
                top_k=top_k,
                score_threshold=score_threshold
            )
        except RetrieverError as e:
            logger.error(f"Retrieval failed: {e}")
            raise GeneratorError(f"Failed to retrieve context: {e}")
        
        # Step 2: Convert to code snippets and source references
        snippets = self._results_to_snippets(retrieval_results)
        sources = self._results_to_sources(retrieval_results)
        
        # Calculate confidence based on retrieval quality
        confidence = self._calculate_confidence(retrieval_results)
        
        # Determine status based on context availability
        if not retrieval_results:
            status = GenerationStatus.NO_CONTEXT
        elif confidence < 0.3:
            status = GenerationStatus.PARTIAL
        else:
            status = GenerationStatus.SUCCESS
        
        # Step 3: Build prompt
        prompt = self._prompt_builder.build_prompt(
            query=query,
            snippets=snippets,
            include_system_prompt=True
        )
        
        # Step 4: Generate response
        try:
            llm_response = await self._llm_client.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
        except LLMClientError as e:
            logger.error(f"LLM generation failed: {e}")
            return GenerationResponse(
                answer="I encountered an error while generating a response. Please try again.",
                status=GenerationStatus.ERROR,
                sources=sources,
                confidence=0.0,
                model=self._llm_client.get_model_name(),
                job_id=job_id,
                query=query,
                error_message=str(e)
            )
        
        # Step 5: Build and return response
        return GenerationResponse(
            answer=llm_response.content,
            status=status,
            sources=sources,
            confidence=confidence,
            model=llm_response.model,
            job_id=job_id,
            query=query,
            tokens_used=llm_response.tokens_used
        )
    
    async def generate_with_context(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        job_id: str = "manual",
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> GenerationResponse:
        """
        Generate a response with manually provided context.
        
        Useful for testing or when context is already available.
        
        Args:
            query: The user's question
            context_chunks: List of chunk dictionaries with content/metadata
            job_id: Job ID for reference
            max_tokens: Maximum tokens in response
            temperature: LLM sampling temperature
            
        Returns:
            GenerationResponse with answer and metadata
        """
        # Convert chunks to snippets
        snippets = [
            CodeSnippet(
                file_path=chunk.get("file_path", "unknown"),
                content=chunk.get("content", ""),
                language=chunk.get("language", "text"),
                start_line=chunk.get("start_line", 1),
                end_line=chunk.get("end_line", 1),
                score=chunk.get("score", 0.0)
            )
            for chunk in context_chunks
        ]
        
        # Build sources
        sources = [
            SourceReference(
                file_path=chunk.get("file_path", "unknown"),
                start_line=chunk.get("start_line", 1),
                end_line=chunk.get("end_line", 1),
                language=chunk.get("language", "text"),
                relevance_score=chunk.get("score", 0.0),
                snippet_preview=chunk.get("content", "")[:200]
            )
            for chunk in context_chunks
        ]
        
        # Build prompt and generate
        prompt = self._prompt_builder.build_prompt(
            query=query,
            snippets=snippets,
            include_system_prompt=True
        )
        
        try:
            llm_response = await self._llm_client.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
        except LLMClientError as e:
            return GenerationResponse(
                answer="Error generating response.",
                status=GenerationStatus.ERROR,
                sources=sources,
                confidence=0.0,
                model=self._llm_client.get_model_name(),
                job_id=job_id,
                query=query,
                error_message=str(e)
            )
        
        confidence = 0.8 if snippets else 0.2
        status = GenerationStatus.SUCCESS if snippets else GenerationStatus.NO_CONTEXT
        
        return GenerationResponse(
            answer=llm_response.content,
            status=status,
            sources=sources,
            confidence=confidence,
            model=llm_response.model,
            job_id=job_id,
            query=query,
            tokens_used=llm_response.tokens_used
        )
    
    def _results_to_snippets(
        self,
        results: List[RetrievalResult]
    ) -> List[CodeSnippet]:
        """Convert retrieval results to code snippets."""
        return [
            CodeSnippet(
                file_path=r.file_path,
                content=r.content,
                language=r.language or "text",
                start_line=r.start_line or 1,
                end_line=r.end_line or 1,
                score=r.score
            )
            for r in results
        ]
    
    def _results_to_sources(
        self,
        results: List[RetrievalResult]
    ) -> List[SourceReference]:
        """Convert retrieval results to source references."""
        return [
            SourceReference(
                file_path=r.file_path,
                start_line=r.start_line or 1,
                end_line=r.end_line or 1,
                language=r.language or "text",
                relevance_score=r.score,
                snippet_preview=r.content[:200] if r.content else ""
            )
            for r in results
        ]
    
    def _calculate_confidence(
        self,
        results: List[RetrievalResult]
    ) -> float:
        """
        Calculate confidence score based on retrieval quality.
        
        Factors:
        - Number of results
        - Average relevance scores
        - Score distribution
        """
        if not results:
            return 0.0
        
        # Average score
        avg_score = sum(r.score for r in results) / len(results)
        
        # Normalize score (handle negative scores from mock embeddings)
        # Assuming scores range from -1 to 1, normalize to 0-1
        normalized_avg = (avg_score + 1) / 2
        
        # Factor in number of results (more is better, up to a point)
        result_factor = min(len(results) / 5, 1.0)
        
        # Combined confidence
        confidence = (normalized_avg * 0.7) + (result_factor * 0.3)
        
        # Clamp to 0-1 range
        return max(0.0, min(1.0, confidence))

    async def generate_documentation(
        self,
        job_id: str,
        doc_type: str = "README",
        repo_name: str = "",
        repo_owner: str = "",
        top_k: int = 5,
        max_tokens: int = 256,
        temperature: float = 0.25
    ) -> GenerationResponse:
        """
        Generate structured documentation (README, API docs, etc.) for a codebase.
        
        Args:
            job_id: Job ID to generate docs for
            doc_type: Type of documentation (README, API, ARCHITECTURE, DETAILED)
            repo_name: Repository name for context
            repo_owner: Repository owner for context
            top_k: Number of code chunks to retrieve (higher for full docs)
            max_tokens: Max tokens (auto-adjusted for DETAILED mode)
            temperature: LLM temperature
            
        Note:
            DETAILED mode automatically uses higher token limit (2048) and
            retrieves more context chunks (top_k=15) for comprehensive docs.
        """
        # Auto-adjust parameters for DETAILED mode
        if doc_type.upper() == "DETAILED":
            max_tokens = 2048  # Much higher for long-form docs
            top_k = 15  # More context for comprehensive coverage
            temperature = 0.4  # Slightly higher for more natural writing
        
        from string import Template
        from src.generation.templates import DOC_TYPE_PROMPTS, CONTEXT_SNIPPET_TEMPLATE
        
        logger.info(f"Generating {doc_type} documentation for job {job_id}")
        
        # Get the appropriate prompt template
        doc_type_upper = doc_type.upper()
        if doc_type_upper not in DOC_TYPE_PROMPTS:
            raise GeneratorError(f"Unsupported doc_type: {doc_type}. Supported: {list(DOC_TYPE_PROMPTS.keys())}")
        
        prompt_template = DOC_TYPE_PROMPTS[doc_type_upper]
        
        # Step 1: Retrieve ALL chunks for comprehensive documentation
        # Use a broad query to get representative samples
        broad_queries = [
            "main entry point",
            "core logic",
            "configuration"
        ]
        
        all_results = []
        seen_paths = set()
        
        for query in broad_queries:
            try:
                results = await self._retriever.retrieve(
                    query=query,
                    job_id=job_id,
                    top_k=top_k // len(broad_queries) + 2
                )
                for r in results:
                    # Deduplicate by file path
                    if r.file_path not in seen_paths:
                        all_results.append(r)
                        seen_paths.add(r.file_path)
            except RetrieverError:
                continue
        
        # If no results from queries, try getting any chunks
        if not all_results:
            try:
                all_results = await self._retriever.retrieve(
                    query="code implementation",
                    job_id=job_id,
                    top_k=top_k
                )
            except RetrieverError as e:
                logger.error(f"Retrieval failed: {e}")
                raise GeneratorError(f"Failed to retrieve context: {e}")
        
        # Step 2: Build code snippets section
        snippets = self._results_to_snippets(all_results[:top_k])
        sources = self._results_to_sources(all_results[:top_k])
        
        # Format code snippets for the prompt
        formatted_snippets = []
        for i, snippet in enumerate(snippets):
            snippet_text = Template(CONTEXT_SNIPPET_TEMPLATE).safe_substitute(
                file_path=snippet.file_path,
                language=snippet.language,
                start_line=snippet.start_line,
                end_line=snippet.end_line,
                score=f"{snippet.score:.2%}" if snippet.score else "N/A",
                content=snippet.content
            )
            formatted_snippets.append(snippet_text)
        
        code_context = "\n\n".join(formatted_snippets)
        
        # Step 3: Build the full prompt
        full_prompt = Template(prompt_template).safe_substitute(
            code_snippets=code_context,
            repo_name=repo_name or "Unknown Repository",
            repo_owner=repo_owner or "Unknown"
        )
        
        # Step 4: Generate documentation
        try:
            llm_response = await self._llm_client.generate(
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
        except LLMClientError as e:
            logger.error(f"LLM generation failed: {e}")
            return GenerationResponse(
                answer="Failed to generate documentation. Please try again.",
                status=GenerationStatus.ERROR,
                sources=sources,
                confidence=0.0,
                model=self._llm_client.get_model_name(),
                job_id=job_id,
                query=f"Generate {doc_type}",
                error_message=str(e)
            )
        
        # Calculate confidence
        confidence = self._calculate_confidence(all_results[:top_k])
        status = GenerationStatus.SUCCESS if all_results else GenerationStatus.NO_CONTEXT
        
        return GenerationResponse(
            answer=llm_response.content,
            status=status,
            sources=sources,
            confidence=confidence,
            model=llm_response.model,
            job_id=job_id,
            query=f"Generate {doc_type}",
            tokens_used=llm_response.tokens_used
        )


# =============================================================================
# Factory Functions
# =============================================================================

_generator: Optional[Generator] = None


def get_generator() -> Generator:
    """Get or create the default generator singleton."""
    global _generator
    if _generator is None:
        _generator = Generator()
    return _generator


async def generate_answer(
    query: str,
    job_id: str,
    top_k: int = 5,
    **kwargs
) -> GenerationResponse:
    """Convenience function for quick generation."""
    generator = get_generator()
    return await generator.generate(
        query=query,
        job_id=job_id,
        top_k=top_k,
        **kwargs
    )
