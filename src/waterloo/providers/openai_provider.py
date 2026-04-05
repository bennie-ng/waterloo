"""OpenAI-compatible chat completions (cloud)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from waterloo.providers.base import ChatProvider


class OpenAICompatibleProvider(ChatProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        default_model: str,
        timeout: float = 120.0,
    ) -> None:
        self._api_key = api_key
        self._base = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout

    def complete(self, messages: list[dict[str, str]], *, model: str | None = None) -> str:
        m = model or self._default_model
        url = f"{self._base}/chat/completions"
        payload: dict[str, Any] = {
            "model": m,
            "messages": messages,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        choices = data.get("choices") or []
        if not choices:
            return json.dumps(data)[:2000]
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        if content is None:
            return json.dumps(data)[:2000]
        return str(content)
