"""Abstract chat provider."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ChatProvider(ABC):
    """Minimal chat completion interface."""

    name: str

    @abstractmethod
    def complete(self, messages: list[dict[str, str]], *, model: str | None = None) -> str:
        """Return assistant message content for the given OpenAI-style messages."""
