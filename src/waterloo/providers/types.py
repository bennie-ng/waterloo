"""Structured chat completion results (tool calls)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NormalizedToolCall:
    """Single tool invocation from an assistant message."""

    id: str
    name: str
    arguments: str  # JSON object string


@dataclass(frozen=True)
class ChatTurnResult:
    """
    One model response: assistant `message` dict suitable to append to `messages`,
    plus a convenience flag when tools must run.
    """

    message: dict[str, Any]
    tool_calls: tuple[NormalizedToolCall, ...]
