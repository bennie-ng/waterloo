"""Tests for guarded tools (Given / When / Then style)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from waterloo import tools as t


def test_given_path_outside_root_when_resolve_then_raises():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "inside.txt").write_text("ok", encoding="utf-8")
        outside = Path(tmp).parent
        with pytest.raises(t.ToolError):
            t.resolve_path_under_root(str(outside / "nope"), root)


def test_given_relative_file_when_resolve_then_reads_inside_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        p = root / "a" / "b.txt"
        p.parent.mkdir(parents=True)
        p.write_text("hello", encoding="utf-8")
        resolved = t.resolve_path_under_root("a/b.txt", root)
        assert resolved == p.resolve()
        assert t.read_text_file(resolved, max_bytes=100) == "hello"


def test_given_git_status_when_allowlist_then_allowed():
    allowed = frozenset({"git", "ls"})
    assert t.is_command_allowed("git status", allowed) is True


def test_given_rm_rf_when_allowlist_then_not_allowed():
    allowed = frozenset({"git", "ls"})
    assert t.is_command_allowed("rm -rf /", allowed) is False


def test_given_tools_local_only_when_mode_cloud_then_not_permitted():
    assert t.tools_permitted_for_mode("cloud", tools_local_only=True) is False


def test_given_tools_local_only_when_mode_local_then_permitted():
    assert t.tools_permitted_for_mode("local", tools_local_only=True) is True


def test_given_tools_local_only_disabled_when_mode_cloud_then_permitted():
    assert t.tools_permitted_for_mode("cloud", tools_local_only=False) is True


def test_given_no_tool_root_env_when_tool_root_then_home_waterloo_sandbox(monkeypatch, tmp_path):
    """Given WATERLOO_TOOL_ROOT unset, when tool_root(), then <HOME>/.waterloo/sandbox."""
    monkeypatch.delenv("WATERLOO_TOOL_ROOT", raising=False)
    monkeypatch.delenv("WATERLOO_WORKSPACE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    got = t.tool_root()
    expected = (tmp_path / ".waterloo" / "sandbox").resolve()
    assert got == expected
    assert got.is_dir()


def test_given_echo_command_when_run_allowlisted_then_stdout():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        code, out, err = t.run_allowlisted_command(
            "echo hello",
            cwd=root,
            allowed=frozenset({"echo"}),
        )
        assert code == 0
        assert "hello" in out
        assert err == ""
