"""LLM Provider Factory.

Creates LLM provider instances based on configuration.
"""

from typing import Any

from app.models.module_converter import LLMConfiguration, LLMProvider
from app.services.llm.base import BaseLLMProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.ollama_provider import OllamaProvider


class LLMProviderError(Exception):
    """Error related to LLM providers."""

    pass


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    _providers: dict[str, type[BaseLLMProvider]] = {
        LLMProvider.OPENAI.value: OpenAIProvider,
        LLMProvider.ANTHROPIC.value: AnthropicProvider,
        LLMProvider.OLLAMA.value: OllamaProvider,
        # Azure uses OpenAI provider with different endpoint
        LLMProvider.AZURE_OPENAI.value: OpenAIProvider,
    }

    @classmethod
    def register_provider(
        cls,
        provider_name: str,
        provider_class: type[BaseLLMProvider],
    ) -> None:
        """Register a custom provider.

        Args:
            provider_name: Name of the provider
            provider_class: Provider class implementing BaseLLMProvider
        """
        cls._providers[provider_name] = provider_class

    @classmethod
    def create_from_config(
        cls,
        config: LLMConfiguration,
        decrypted_api_key: str,
    ) -> BaseLLMProvider:
        """Create a provider instance from configuration.

        Args:
            config: LLM configuration from database
            decrypted_api_key: Decrypted API key

        Returns:
            Configured provider instance

        Raises:
            LLMProviderError: If provider is not supported
        """
        provider_name = (
            config.provider.value
            if hasattr(config.provider, "value")
            else config.provider
        )

        if provider_name not in cls._providers:
            raise LLMProviderError(f"Unsupported provider: {provider_name}")

        provider_class = cls._providers[provider_name]

        # Extract additional config
        extra_config = config.config or {}

        return provider_class(
            api_key=decrypted_api_key,
            model=config.model_name,
            api_endpoint=config.api_endpoint,
            **extra_config,
        )

    @classmethod
    def create(
        cls,
        provider: str,
        api_key: str,
        model: str,
        api_endpoint: str | None = None,
        **kwargs: Any,
    ) -> BaseLLMProvider:
        """Create a provider instance directly.

        Args:
            provider: Provider name
            api_key: API key
            model: Model name
            api_endpoint: Optional custom endpoint
            **kwargs: Additional provider-specific options

        Returns:
            Configured provider instance

        Raises:
            LLMProviderError: If provider is not supported
        """
        if provider not in cls._providers:
            raise LLMProviderError(f"Unsupported provider: {provider}")

        provider_class = cls._providers[provider]
        return provider_class(
            api_key=api_key,
            model=model,
            api_endpoint=api_endpoint,
            **kwargs,
        )

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider names."""
        return list(cls._providers.keys())
