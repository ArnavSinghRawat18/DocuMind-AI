"""
Prompt templates module for DocuMind AI.
Defines system prompts, context injection templates, and anti-hallucination rules.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from string import Template

from src.utils.logger import get_logger

logger = get_logger("documind.templates")


# =============================================================================
# System Prompts
# =============================================================================

SYSTEM_PROMPT_CODE_ASSISTANT = """You are DocuMind AI, an intelligent code documentation assistant. Your primary purpose is to help developers understand and navigate codebases by providing accurate, helpful explanations based on the code context provided to you.

## Core Principles

1. **Accuracy First**: Only provide information that is directly supported by the code context given to you. Never invent or assume functionality that isn't present in the provided code.

2. **Source Attribution**: When explaining code, reference specific files, functions, classes, or line numbers from the context.

3. **Clarity**: Explain technical concepts in a clear, structured manner. Use code examples from the context when helpful.

4. **Honesty About Limitations**: If the provided context doesn't contain enough information to fully answer a question, clearly state what you can and cannot determine.

## Response Guidelines

- Start with a direct answer to the question
- Support your answer with specific references to the code context
- Use Markdown formatting for code blocks and structure
- If the question cannot be answered from the context, say so explicitly

## Anti-Hallucination Rules

- NEVER invent function names, class names, or file paths that aren't in the context
- NEVER describe code behavior that isn't evident from the provided snippets
- If asked about code not in the context, respond: "I don't have information about that in the provided code context"
- NEVER make up line numbers or file locations"""


SYSTEM_PROMPT_MINIMAL = """You are DocuMind AI, a code documentation assistant. Answer questions based ONLY on the provided code context. If information isn't in the context, say so. Always cite specific files and code when possible."""


# =============================================================================
# Context Injection Templates  
# =============================================================================

CONTEXT_TEMPLATE = """## Code Context

The following code snippets are relevant to your question. Each snippet includes the file path, programming language, and line numbers.

$code_snippets

---

## Question

$query"""


CONTEXT_SNIPPET_TEMPLATE = """### $file_path
**Language:** $language | **Lines:** $start_line-$end_line | **Relevance:** $score

```$language
$content
```
"""


NO_CONTEXT_TEMPLATE = """## Notice

No relevant code snippets were found for your question. This could mean:
1. The codebase hasn't been indexed yet
2. The question doesn't relate to the indexed code
3. Try rephrasing your question with specific function or file names

## Question

$query

Please let me know if you'd like me to search differently or if you can provide more specific terms."""


# =============================================================================
# Prompt Builder Classes
# =============================================================================

@dataclass
class CodeSnippet:
    """Represents a code snippet for prompt injection."""
    file_path: str
    content: str
    language: str = "text"
    start_line: int = 1
    end_line: int = 1
    score: float = 0.0
    
    def format(self) -> str:
        """Format the snippet for prompt injection."""
        template = Template(CONTEXT_SNIPPET_TEMPLATE)
        return template.safe_substitute(
            file_path=self.file_path,
            language=self.language or "text",
            start_line=self.start_line,
            end_line=self.end_line,
            score=f"{self.score:.2%}" if self.score else "N/A",
            content=self.content
        )


class PromptBuilder:
    """
    Builder class for constructing LLM prompts.
    Handles system prompts, context injection, and formatting.
    """
    
    def __init__(
        self,
        system_prompt: str = SYSTEM_PROMPT_CODE_ASSISTANT,
        max_context_tokens: int = 3000
    ):
        """
        Initialize the prompt builder.
        
        Args:
            system_prompt: The system prompt to use
            max_context_tokens: Maximum tokens for context (approximate)
        """
        self.system_prompt = system_prompt
        self.max_context_tokens = max_context_tokens
        
    def build_prompt(
        self,
        query: str,
        snippets: List[CodeSnippet],
        include_system_prompt: bool = True
    ) -> str:
        """
        Build a complete prompt with context and query.
        
        Args:
            query: The user's question
            snippets: List of relevant code snippets
            include_system_prompt: Whether to include system prompt
            
        Returns:
            Formatted prompt string
        """
        # Build context section
        if snippets:
            context = self._build_context_section(snippets)
            user_prompt = Template(CONTEXT_TEMPLATE).safe_substitute(
                code_snippets=context,
                query=query
            )
        else:
            user_prompt = Template(NO_CONTEXT_TEMPLATE).safe_substitute(
                query=query
            )
        
        # Combine with system prompt if requested
        if include_system_prompt:
            return f"{self.system_prompt}\n\n{user_prompt}"
        return user_prompt
    
    def _build_context_section(self, snippets: List[CodeSnippet]) -> str:
        """Build the context section from code snippets."""
        formatted_snippets = []
        total_length = 0
        
        # Approximate token limit (rough: 4 chars per token)
        char_limit = self.max_context_tokens * 4
        
        for snippet in snippets:
            formatted = snippet.format()
            
            # Check if adding this snippet would exceed limit
            if total_length + len(formatted) > char_limit:
                logger.warning("Context truncated due to token limit")
                break
            
            formatted_snippets.append(formatted)
            total_length += len(formatted)
        
        return "\n".join(formatted_snippets)
    
    def build_messages(
        self,
        query: str,
        snippets: List[CodeSnippet]
    ) -> List[Dict[str, str]]:
        """
        Build messages in OpenAI chat format.
        
        Args:
            query: The user's question
            snippets: List of relevant code snippets
            
        Returns:
            List of message dictionaries
        """
        # Build context section
        if snippets:
            context = self._build_context_section(snippets)
            user_content = Template(CONTEXT_TEMPLATE).safe_substitute(
                code_snippets=context,
                query=query
            )
        else:
            user_content = Template(NO_CONTEXT_TEMPLATE).safe_substitute(
                query=query
            )
        
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content}
        ]


# =============================================================================
# Utility Functions
# =============================================================================

def create_snippet_from_retrieval(result: Dict[str, Any]) -> CodeSnippet:
    """
    Create a CodeSnippet from a retrieval result.
    
    Args:
        result: Retrieval result dictionary with chunk data
        
    Returns:
        CodeSnippet instance
    """
    return CodeSnippet(
        file_path=result.get("file_path", "unknown"),
        content=result.get("content", ""),
        language=result.get("language", "text"),
        start_line=result.get("start_line", 1),
        end_line=result.get("end_line", 1),
        score=result.get("score", 0.0)
    )


def get_prompt_builder(
    minimal: bool = False,
    max_context_tokens: int = 3000
) -> PromptBuilder:
    """
    Factory function to get a prompt builder.
    
    Args:
        minimal: Use minimal system prompt
        max_context_tokens: Maximum context tokens
        
    Returns:
        Configured PromptBuilder instance
    """
    system_prompt = SYSTEM_PROMPT_MINIMAL if minimal else SYSTEM_PROMPT_CODE_ASSISTANT
    return PromptBuilder(
        system_prompt=system_prompt,
        max_context_tokens=max_context_tokens
    )


# Default prompt builder instance
_default_builder: Optional[PromptBuilder] = None


def get_default_prompt_builder() -> PromptBuilder:
    """Get or create the default prompt builder singleton."""
    global _default_builder
    if _default_builder is None:
        _default_builder = get_prompt_builder()
    return _default_builder
