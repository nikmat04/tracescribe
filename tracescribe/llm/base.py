"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMError(Exception):
    """Raised when the LLM provider encounters an error."""


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send *prompt* to the LLM and return the generated text string."""
