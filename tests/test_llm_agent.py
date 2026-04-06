"""Tests for LLM tool parsing, executor, and agent loop (Given / When / Then style)."""

from __future__ import annotations

from typing import Any

from waterloo.agent_loop import run_agent_turn
from waterloo.providers.base import ChatProvider
from waterloo.providers.parse import result_from_openai_message
from waterloo.providers.types import ChatTurnResult, NormalizedToolCall
from waterloo.tool_executor import dispatch_tool


def test_given_openai_message_with_tool_calls_when_parse_then_normalized():
    msg = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_abc",
                "type": "function",
                "function": {"name": "read_file", "arguments": '{"path":"f.txt"}'},
            }
        ],
    }
    r = result_from_openai_message(msg)
    assert len(r.tool_calls) == 1
    assert r.tool_calls[0].name == "read_file"
    assert "f.txt" in r.tool_calls[0].arguments


def test_given_home_with_file_when_dispatch_read_then_content(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("WATERLOO_WORKSPACE", raising=False)
    monkeypatch.delenv("WATERLOO_TOOL_ROOT", raising=False)
    sandbox = tmp_path / ".waterloo" / "sandbox"
    sandbox.mkdir(parents=True)
    (sandbox / "note.txt").write_text("alpha", encoding="utf-8")
    out = dispatch_tool(
        "read_file",
        '{"path": "note.txt"}',
        confirm_run=lambda _: True,
    )
    assert out == "alpha"


def test_given_run_echo_when_dispatch_then_output(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("WATERLOO_WORKSPACE", raising=False)
    monkeypatch.delenv("WATERLOO_TOOL_ROOT", raising=False)
    (tmp_path / ".waterloo" / "sandbox").mkdir(parents=True)
    monkeypatch.setenv("WATERLOO_AUTO_APPROVE_TOOLS", "1")
    out = dispatch_tool(
        "run_command",
        '{"command": "echo hi"}',
        confirm_run=lambda _: False,
    )
    assert "exit 0" in out
    assert "hi" in out


class _SeqProvider(ChatProvider):
    name = "seq"

    def __init__(self, results: list[ChatTurnResult]) -> None:
        self._results = results
        self.i = 0

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None,
        model: str | None = None,
    ) -> ChatTurnResult:
        r = self._results[self.i]
        self.i += 1
        return r


def test_given_tool_then_text_when_agent_loop_then_final_string(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("WATERLOO_WORKSPACE", raising=False)
    monkeypatch.delenv("WATERLOO_TOOL_ROOT", raising=False)
    sandbox = tmp_path / ".waterloo" / "sandbox"
    sandbox.mkdir(parents=True)
    (sandbox / "x.txt").write_text("hello", encoding="utf-8")
    monkeypatch.setenv("WATERLOO_AUTO_APPROVE_TOOLS", "1")
    tc = NormalizedToolCall(id="call_1", name="read_file", arguments='{"path":"x.txt"}')
    r1 = ChatTurnResult(
        message={
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": '{"path":"x.txt"}',
                    },
                }
            ],
        },
        tool_calls=(tc,),
    )
    r2 = ChatTurnResult(
        message={"role": "assistant", "content": "Done reading."},
        tool_calls=(),
    )
    p = _SeqProvider([r1, r2])
    out = run_agent_turn(
        p,
        [{"role": "user", "content": "read x.txt"}],
        model=None,
        use_tools=True,
        max_steps=8,
        confirm_run=lambda _: True,
    )
    assert "Done reading" in out
    assert p.i == 2


class _LoopyProvider(ChatProvider):
    name = "loopy"

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None,
        model: str | None = None,
    ) -> ChatTurnResult:
        tc = NormalizedToolCall(
            id="call_x",
            name="read_file",
            arguments='{"path":"missing.txt"}',
        )
        return ChatTurnResult(
            message={
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_x",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path":"missing.txt"}',
                        },
                    }
                ],
            },
            tool_calls=(tc,),
        )


def test_given_repeated_tools_when_max_steps_then_stops(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("WATERLOO_WORKSPACE", raising=False)
    monkeypatch.delenv("WATERLOO_TOOL_ROOT", raising=False)
    (tmp_path / ".waterloo" / "sandbox").mkdir(parents=True)
    monkeypatch.setenv("WATERLOO_AUTO_APPROVE_TOOLS", "1")
    out = run_agent_turn(
        _LoopyProvider(),
        [{"role": "user", "content": "x"}],
        model=None,
        use_tools=True,
        max_steps=3,
        confirm_run=lambda _: True,
    )
    assert "exceeded maximum agent steps" in out
