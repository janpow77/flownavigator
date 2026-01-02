"""Anthropic LLM Provider.

Supports Anthropic Claude API.
"""

import time
from typing import Any, AsyncIterator

import httpx

from app.services.llm.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    MessageRole,
    StreamChunk,
)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider implementation."""

    DEFAULT_API_ENDPOINT = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _get_endpoint(self) -> str:
        """Get the API endpoint."""
        return self.api_endpoint or self.DEFAULT_API_ENDPOINT

    def _format_messages(
        self, messages: list[LLMMessage]
    ) -> tuple[str | None, list[dict[str, str]]]:
        """Format messages for Anthropic API.

        Returns:
            Tuple of (system_prompt, messages)
        """
        system_prompt = None
        formatted_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt = msg.content
            else:
                formatted_messages.append(
                    {
                        "role": msg.role.value,
                        "content": msg.content,
                    }
                )

        return system_prompt, formatted_messages

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using Anthropic API."""
        start_time = time.time()
        system_prompt, formatted_messages = self._format_messages(messages)

        request_data = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            request_data["system"] = system_prompt

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._get_endpoint()}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": self.API_VERSION,
                    "Content-Type": "application/json",
                },
                json=request_data,
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start_time) * 1000
        usage = data.get("usage", {})

        # Extract text from content blocks
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        return LLMResponse(
            content=content,
            model=data["model"],
            provider=self.provider_name,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            latency_ms=latency_ms,
            finish_reason=data.get("stop_reason"),
            metadata={"id": data.get("id")},
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion using Anthropic API."""
        system_prompt, formatted_messages = self._format_messages(messages)

        request_data = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if system_prompt:
            request_data["system"] = system_prompt

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._get_endpoint()}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": self.API_VERSION,
                    "Content-Type": "application/json",
                },
                json=request_data,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            import json

                            data = json.loads(line[6:])
                            event_type = data.get("type")

                            if event_type == "content_block_delta":
                                delta = data.get("delta", {})
                                if text := delta.get("text"):
                                    yield StreamChunk(content=text)
                            elif event_type == "message_stop":
                                yield StreamChunk(content="", is_final=True)
                                break
                        except Exception:
                            continue
