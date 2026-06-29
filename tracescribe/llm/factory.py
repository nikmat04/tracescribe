"""Factory that returns the correct LLMProvider based on config."""

from __future__ import annotations

from tracescribe.config import LLMConfig
from tracescribe.llm.base import LLMError, LLMProvider


def get_llm_provider(config: LLMConfig) -> LLMProvider:
    """Instantiate and return the LLM provider specified by *config*.

    Raises:
        LLMError: if *config.provider* is not a supported provider name.
    """
    if config.provider == "ollama":
        from tracescribe.llm.ollama_provider import OllamaProvider

        return OllamaProvider(model=config.model, base_url=config.base_url)

    raise LLMError(
        f"Unknown LLM provider: {config.provider!r}. Supported: ollama"
    )
