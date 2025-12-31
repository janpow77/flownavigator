"""Ollama LLM Provider.

Supports local Ollama instance.
"""

import time
from typing import Any, AsyncIterator

import httpx

from app.services.llm.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    StreamChunk,
)


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider implementation."""

    DEFAULT_API_ENDPOINT = "http://localhost:11434"

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _get_endpoint(self) -> str:
        """Get the API endpoint."""
        return self.api_endpoint or self.DEFAULT_API_ENDPOINT

    def _format_messages(self, messages: list[LLMMessage]) -> list[dict[str, str]]:
        """Format messages for Ollama API."""
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
        """Generate a completion using Ollama API."""
        start_time = time.time()

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self._get_endpoint()}/api/chat",
                json={
                    "model": self.model,
                    "messages": self._format_messages(messages),
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start_time) * 1000
        message = data.get("message", {})

        return LLMResponse(
            content=message.get("content", ""),
            model=data.get("model", self.model),
            provider=self.provider_name,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            latency_ms=latency_ms,
            finish_reason=data.get("done_reason"),
            metadata={
                "total_duration": data.get("total_duration"),
                "load_duration": data.get("load_duration"),
            },
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion using Ollama API."""
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self._get_endpoint()}/api/chat",
                json={
                    "model": self.model,
                    "messages": self._format_messages(messages),
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    try:
                        import json
                        data = json.loads(line)
                        message = data.get("message", {})
                        if content := message.get("content"):
                            yield StreamChunk(content=content)
                        if data.get("done"):
                            yield StreamChunk(content="", is_final=True)
                            break
                    except Exception:
                        continue

    async def validate_connection(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if server is running
                response = await client.get(f"{self._get_endpoint()}/api/tags")
                if response.status_code != 200:
                    return False

                # Check if model exists
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return self.model in models or f"{self.model}:latest" in models
        except Exception:
            return False
