"""OpenAI LLM Provider.

Supports OpenAI API (GPT-4, GPT-3.5, etc.)
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


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider implementation."""

    DEFAULT_API_ENDPOINT = "https://api.openai.com/v1"

    @property
    def provider_name(self) -> str:
        return "openai"

    def _get_endpoint(self) -> str:
        """Get the API endpoint."""
        return self.api_endpoint or self.DEFAULT_API_ENDPOINT

    def _format_messages(self, messages: list[LLMMessage]) -> list[dict[str, str]]:
        """Format messages for OpenAI API."""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using OpenAI API."""
        start_time = time.time()

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._get_endpoint()}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": self._format_messages(messages),
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs,
                },
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start_time) * 1000
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=data["model"],
            provider=self.provider_name,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=latency_ms,
            finish_reason=choice.get("finish_reason"),
            metadata={"id": data.get("id")},
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion using OpenAI API."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._get_endpoint()}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": self._format_messages(messages),
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                    **kwargs,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            yield StreamChunk(content="", is_final=True)
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            if content := delta.get("content"):
                                yield StreamChunk(content=content)
                        except Exception:
                            continue
