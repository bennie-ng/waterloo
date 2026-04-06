"""Normalize provider responses into ChatTurnResult."""

from __future__ import annotations

import json
from typing import Any

from waterloo.providers.types import ChatTurnResult, NormalizedToolCall


def result_from_openai_message(msg: dict[str, Any]) -> ChatTurnResult:
    """Build ChatTurnResult from OpenAI chat.completions `message` object."""
    role = msg.get("role") or "assistant"
    content = msg.get("content")
    raw_tcs = msg.get("tool_calls")
    tool_calls: list[NormalizedToolCall] = []
    if raw_tcs:
        for tc in raw_tcs:
            if not isinstance(tc, dict):
                continue
            fn = tc.get("function") or {}
            name = str(fn.get("name") or "")
            args = fn.get("arguments")
            if isinstance(args, str):
                args_str = args
            elif args is None:
                args_str = "{}"
            else:
                args_str = json.dumps(args)
            tid = str(tc.get("id") or "")
            if not tid:
                continue
            tool_calls.append(NormalizedToolCall(id=tid, name=name, arguments=args_str))
    out_msg: dict[str, Any] = {"role": role, "content": content}
    if raw_tcs:
        out_msg["tool_calls"] = raw_tcs  # preserve provider shape for replay
    return ChatTurnResult(message=out_msg, tool_calls=tuple(tool_calls))


def result_from_ollama_message(msg: dict[str, Any]) -> ChatTurnResult:
    """Build ChatTurnResult from Ollama /api/chat `message` object."""
    role = msg.get("role") or "assistant"
    content = msg.get("content")
    raw_tcs = msg.get("tool_calls")
    tool_calls: list[NormalizedToolCall] = []
    openai_style_tcs: list[dict[str, Any]] = []
    if raw_tcs:
        for i, tc in enumerate(raw_tcs):
            if not isinstance(tc, dict):
                continue
            fn = tc.get("function") or {}
            name = str(fn.get("name") or "")
            args = fn.get("arguments")
            if isinstance(args, dict):
                args_str = json.dumps(args)
            elif isinstance(args, str):
                args_str = args
            else:
                args_str = "{}"
            tid = str(tc.get("id") or f"ollama-call-{i}")
            tool_calls.append(NormalizedToolCall(id=tid, name=name, arguments=args_str))
            openai_style_tcs.append(
                {
                    "id": tid,
                    "type": "function",
                    "function": {"name": name, "arguments": args_str},
                }
            )
    out_msg: dict[str, Any] = {"role": role, "content": content}
    if tool_calls:
        out_msg["tool_calls"] = openai_style_tcs
    return ChatTurnResult(message=out_msg, tool_calls=tuple(tool_calls))
