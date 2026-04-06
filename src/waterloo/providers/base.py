"""Abstract chat provider."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from waterloo.providers.types import ChatTurnResult


class ChatProvider(ABC):
    """Chat completion with optional tool use."""

    name: str

    def complete(self, messages: list[dict[str, Any]], *, model: str | None = None) -> str:
        """Plain completion (no tools sent to the API)."""
        r = self.chat_with_tools(messages, tools=None, model=model)
        c = r.message.get("content")
        return str(c) if c is not None else ""

    @abstractmethod
    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None,
        model: str | None = None,
    ) -> ChatTurnResult:
        """One completion turn; may include tool calls to execute next."""
