"""Ollama local inference."""

from __future__ import annotations

import json
from typing import Any

import httpx

from waterloo.providers.base import ChatProvider
from waterloo.providers.parse import result_from_ollama_message
from waterloo.providers.types import ChatTurnResult


class OllamaProvider(ChatProvider):
    name = "ollama"

    def __init__(self, base_url: str, default_model: str, timeout: float = 120.0) -> None:
        self._base = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout

    @property
    def base_url(self) -> str:
        return self._base

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None,
        model: str | None = None,
    ) -> ChatTurnResult:
        m = model or self._default_model
        payload: dict[str, Any] = {
            "model": m,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        url = f"{self._base}/api/chat"
        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        msg = data.get("message") or {}
        if not msg.get("content") and not msg.get("tool_calls"):
            content = json.dumps(data)[:2000]
            return ChatTurnResult(
                message={"role": "assistant", "content": content},
                tool_calls=(),
            )
        return result_from_ollama_message(msg)
