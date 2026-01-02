"""Base LLM Provider Interface.

Defines the abstract interface for all LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator


class MessageRole(str, Enum):
    """Message role in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """A message in the conversation."""

    role: MessageRole
    content: str
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    provider: str

    # Token usage
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # Timing
    latency_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Additional metadata
    finish_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def estimated_cost(self) -> float:
        """Estimate cost based on token usage (simplified)."""
        # Approximate costs per 1K tokens (varies by model)
        cost_per_1k_prompt = 0.01
        cost_per_1k_completion = 0.03
        return (self.prompt_tokens / 1000) * cost_per_1k_prompt + (
            self.completion_tokens / 1000
        ) * cost_per_1k_completion


@dataclass
class StreamChunk:
    """A chunk from a streaming response."""

    content: str
    is_final: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must implement this interface.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        api_endpoint: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the provider.

        Args:
            api_key: API key for authentication
            model: Model name/ID to use
            api_endpoint: Optional custom API endpoint
            **kwargs: Additional provider-specific options
        """
        self.api_key = api_key
        self.model = model
        self.api_endpoint = api_endpoint
        self.options = kwargs

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion for the given messages.

        Args:
            messages: List of messages in the conversation
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific options

        Returns:
            LLMResponse with the generated content
        """
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion for the given messages.

        Args:
            messages: List of messages in the conversation
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific options

        Yields:
            StreamChunk with partial content
        """
        ...

    async def validate_connection(self) -> bool:
        """Validate that the provider connection works.

        Returns:
            True if connection is valid
        """
        try:
            # Simple test completion
            response = await self.complete(
                messages=[LLMMessage(role=MessageRole.USER, content="Say 'ok'")],
                max_tokens=10,
            )
            return bool(response.content)
        except Exception:
            return False

    def count_tokens(self, text: str) -> int:
        """Estimate token count for text.

        This is a rough estimate. Override for provider-specific counting.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4
