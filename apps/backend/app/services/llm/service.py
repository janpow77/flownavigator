"""LLM Service.

Main service for interacting with LLM providers with fallback support.
"""

import asyncio
import logging
from typing import Any, AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.module_converter import LLMConfiguration
from app.services.llm.base import LLMMessage, LLMResponse, StreamChunk
from app.services.llm.factory import LLMProviderFactory


logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Error from the LLM service."""

    pass


class LLMService:
    """Service for LLM interactions with fallback support.

    Features:
    - Multi-provider support
    - Automatic fallback on failure
    - Rate limiting
    - Response caching
    - Retry with exponential backoff
    """

    def __init__(
        self,
        db: AsyncSession,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_caching: bool = True,
    ) -> None:
        """Initialize the LLM service.

        Args:
            db: Database session
            max_retries: Maximum retry attempts per provider
            retry_delay: Initial retry delay in seconds
            enable_caching: Whether to cache responses
        """
        self.db = db
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_caching = enable_caching
        self._cache: dict[str, LLMResponse] = {}
        self._rate_limiters: dict[str, asyncio.Semaphore] = {}

    async def _get_configurations(
        self,
        config_id: str | None = None,
    ) -> list[LLMConfiguration]:
        """Get LLM configurations ordered by priority.

        Args:
            config_id: Optional specific configuration ID

        Returns:
            List of configurations to try
        """
        if config_id:
            result = await self.db.execute(
                select(LLMConfiguration)
                .where(LLMConfiguration.id == config_id)
                .where(LLMConfiguration.is_active.is_(True))
            )
            config = result.scalar_one_or_none()
            if not config:
                raise LLMServiceError(f"Configuration not found: {config_id}")
            return [config]

        # Get all active configurations ordered by priority
        result = await self.db.execute(
            select(LLMConfiguration)
            .where(LLMConfiguration.is_active.is_(True))
            .order_by(LLMConfiguration.priority.asc())
        )
        configs = list(result.scalars().all())

        if not configs:
            raise LLMServiceError("No active LLM configurations found")

        return configs

    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key.

        TODO: Implement proper encryption/decryption

        Args:
            encrypted_key: Encrypted API key

        Returns:
            Decrypted API key
        """
        # For now, assume keys are stored as-is (not recommended for production)
        return encrypted_key

    def _get_rate_limiter(self, config: LLMConfiguration) -> asyncio.Semaphore:
        """Get or create rate limiter for a configuration."""
        config_id = str(config.id)
        if config_id not in self._rate_limiters:
            # Allow concurrent requests up to rate limit
            max_concurrent = min(config.requests_per_minute // 10, 10)
            self._rate_limiters[config_id] = asyncio.Semaphore(max_concurrent)
        return self._rate_limiters[config_id]

    def _get_cache_key(
        self,
        messages: list[LLMMessage],
        config_id: str,
        temperature: float,
    ) -> str:
        """Generate cache key for request."""
        content = "|".join(f"{m.role.value}:{m.content}" for m in messages)
        return f"{config_id}:{temperature}:{hash(content)}"

    async def complete(
        self,
        messages: list[LLMMessage],
        config_id: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_cache: bool = True,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion with automatic fallback.

        Args:
            messages: List of messages
            config_id: Optional specific configuration to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            use_cache: Whether to use cached response if available
            **kwargs: Additional options

        Returns:
            LLMResponse from the first successful provider

        Raises:
            LLMServiceError: If all providers fail
        """
        configs = await self._get_configurations(config_id)

        # Check cache
        if use_cache and self.enable_caching:
            cache_key = self._get_cache_key(messages, str(configs[0].id), temperature)
            if cache_key in self._cache:
                logger.debug("Returning cached response")
                return self._cache[cache_key]

        errors: list[tuple[str, Exception]] = []

        for config in configs:
            try:
                response = await self._complete_with_config(
                    config=config,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                # Cache successful response
                if use_cache and self.enable_caching:
                    cache_key = self._get_cache_key(
                        messages, str(config.id), temperature
                    )
                    self._cache[cache_key] = response

                return response

            except Exception as e:
                logger.warning(
                    f"Provider {config.provider} failed: {e}",
                    exc_info=True,
                )
                errors.append((config.provider.value, e))
                continue

        # All providers failed
        error_msg = "; ".join(f"{p}: {e}" for p, e in errors)
        raise LLMServiceError(f"All providers failed: {error_msg}")

    async def _complete_with_config(
        self,
        config: LLMConfiguration,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
        **kwargs: Any,
    ) -> LLMResponse:
        """Complete with a specific configuration and retry logic."""
        api_key = self._decrypt_api_key(config.api_key_encrypted or "")
        provider = LLMProviderFactory.create_from_config(config, api_key)
        rate_limiter = self._get_rate_limiter(config)

        last_error: Exception | None = None
        delay = self.retry_delay

        for attempt in range(self.max_retries):
            try:
                async with rate_limiter:
                    response = await provider.complete(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs,
                    )
                    return response
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.debug(
                        f"Retry {attempt + 1}/{self.max_retries} after {delay}s"
                    )
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff

        raise last_error or LLMServiceError("Unknown error")

    async def stream(
        self,
        messages: list[LLMMessage],
        config_id: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion with automatic fallback.

        Args:
            messages: List of messages
            config_id: Optional specific configuration to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional options

        Yields:
            StreamChunk from the first successful provider

        Raises:
            LLMServiceError: If all providers fail
        """
        configs = await self._get_configurations(config_id)
        errors: list[tuple[str, Exception]] = []

        for config in configs:
            try:
                api_key = self._decrypt_api_key(config.api_key_encrypted or "")
                provider = LLMProviderFactory.create_from_config(config, api_key)

                async for chunk in provider.stream(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                ):
                    yield chunk
                return

            except Exception as e:
                logger.warning(
                    f"Provider {config.provider} streaming failed: {e}",
                    exc_info=True,
                )
                errors.append((config.provider.value, e))
                continue

        # All providers failed
        error_msg = "; ".join(f"{p}: {e}" for p, e in errors)
        raise LLMServiceError(f"All streaming providers failed: {error_msg}")

    async def test_connection(self, config_id: str) -> bool:
        """Test connection for a specific configuration.

        Args:
            config_id: Configuration ID to test

        Returns:
            True if connection is successful
        """
        configs = await self._get_configurations(config_id)
        if not configs:
            return False

        config = configs[0]
        try:
            api_key = self._decrypt_api_key(config.api_key_encrypted or "")
            provider = LLMProviderFactory.create_from_config(config, api_key)
            return await provider.validate_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()

    async def get_default_config(self) -> LLMConfiguration | None:
        """Get the default LLM configuration."""
        result = await self.db.execute(
            select(LLMConfiguration)
            .where(LLMConfiguration.is_default.is_(True))
            .where(LLMConfiguration.is_active.is_(True))
        )
        return result.scalar_one_or_none()
