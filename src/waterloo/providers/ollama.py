"""Ollama local inference."""

from __future__ import annotations

import json
from typing import Any

import httpx

from waterloo.providers.base import ChatProvider


class OllamaProvider(ChatProvider):
    name = "ollama"

    def __init__(self, base_url: str, default_model: str, timeout: float = 120.0) -> None:
        self._base = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout

    @property
    def base_url(self) -> str:
        return self._base

    def complete(self, messages: list[dict[str, str]], *, model: str | None = None) -> str:
        m = model or self._default_model
        payload: dict[str, Any] = {
            "model": m,
            "messages": messages,
            "stream": False,
        }
        url = f"{self._base}/api/chat"
        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        msg = data.get("message") or {}
        content = msg.get("content")
        if content is None:
            return json.dumps(data)[:2000]
        return str(content)
