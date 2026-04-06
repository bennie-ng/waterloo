"""Multi-step tool loop until the model returns plain text."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from waterloo.llm_tools import OPENAI_TOOLS_SPEC
from waterloo.providers.base import ChatProvider
from waterloo.tool_executor import dispatch_tool


def run_agent_turn(
    provider: ChatProvider,
    messages: list[dict[str, Any]],
    *,
    model: str | None,
    use_tools: bool,
    max_steps: int,
    confirm_run: Callable[[str], bool],
    on_tool_event: Callable[[str, str], None] | None = None,
) -> str:
    """
    Either one plain completion (use_tools False) or a tool loop.

    When use_tools is True, sends OPENAI_TOOLS_SPEC to the provider. Appends assistant
    and tool messages until the assistant returns content without tool calls or max_steps.
    """
    if not use_tools:
        return provider.complete(messages, model=model)

    msgs: list[dict[str, Any]] = [dict(x) for x in messages]
    tools = OPENAI_TOOLS_SPEC

    for _step in range(max_steps):
        result = provider.chat_with_tools(msgs, tools=tools, model=model)
        tcs = result.tool_calls

        if not tcs:
            content = result.message.get("content")
            if content is not None:
                return str(content)
            return "error: model returned an empty response"

        msgs.append(result.message)

        for tc in tcs:
            if on_tool_event:
                preview = tc.arguments[:120] + ("…" if len(tc.arguments) > 120 else "")
                on_tool_event(tc.name, preview)
            out = dispatch_tool(tc.name, tc.arguments, confirm_run=confirm_run)
            msgs.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": out,
                }
            )

    return (
        f"Stopped: exceeded maximum agent steps ({max_steps}) without a final text answer."
    )
