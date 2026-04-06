"""OpenAI-compatible chat completions (cloud)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from waterloo.providers.base import ChatProvider
from waterloo.providers.parse import result_from_openai_message
from waterloo.providers.types import ChatTurnResult


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

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None,
        model: str | None = None,
    ) -> ChatTurnResult:
        m = model or self._default_model
        url = f"{self._base}/chat/completions"
        payload: dict[str, Any] = {
            "model": m,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
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
            return ChatTurnResult(
                message={"role": "assistant", "content": json.dumps(data)[:2000]},
                tool_calls=(),
            )
        msg = choices[0].get("message") or {}
        return result_from_openai_message(msg)
