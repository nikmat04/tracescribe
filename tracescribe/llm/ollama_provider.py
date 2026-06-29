"""Ollama LLM provider implementation."""

from __future__ import annotations

import ollama

from tracescribe.llm.base import LLMError, LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url  # e.g. http://localhost:11434

    def generate(self, prompt: str) -> str:
        """Send *prompt* to Ollama and return the response text.

        Raises:
            LLMError: if Ollama is not reachable (connection refused / timeout).
        """
        try:
            client = ollama.Client(host=self.base_url)
            response = client.generate(model=self.model, prompt=prompt)
            return response["response"]
        except Exception as exc:
            # Catch any connection-level error from the ollama SDK / httpx
            if _is_connection_error(exc):
                raise LLMError(
                    "Ollama not running \u2014 start it with: ollama serve"
                ) from exc
            raise


def _is_connection_error(exc: BaseException) -> bool:
    """Return True for network/connection errors regardless of the SDK version."""
    name = type(exc).__name__
    msg = str(exc).lower()
    return (
        "connect" in name.lower()
        or "connection" in msg
        or "refused" in msg
        or "timeout" in msg
        or "unreachable" in msg
        or name in ("ConnectError", "ConnectionError", "ConnectTimeout", "RequestError")
    )
