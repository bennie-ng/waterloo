"""Execute LLM-requested tools using the same guards as slash /read and /run."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from waterloo import config as cfg
from waterloo import tools as t


def dispatch_tool(
    name: str,
    arguments_json: str,
    *,
    confirm_run: Callable[[str], bool],
) -> str:
    """
    Run one tool; returns text for the model (including error lines starting with 'error:').
    """
    try:
        args: Any = json.loads(arguments_json) if arguments_json.strip() else {}
    except json.JSONDecodeError as e:
        return f"error: invalid JSON arguments: {e}"
    if not isinstance(args, dict):
        return "error: arguments must be a JSON object"

    if name == "read_file":
        path = args.get("path", "")
        if not isinstance(path, str):
            return "error: path must be a string"
        root = t.tool_root()
        try:
            p = t.resolve_path_under_root(path, root)
            return t.read_text_file(p, max_bytes=t.max_read_bytes())
        except t.ToolError as e:
            return f"error: {e}"

    if name == "run_command":
        command = args.get("command", "")
        if not isinstance(command, str):
            return "error: command must be a string"
        allowed = t.default_allowed_first_tokens()
        if not t.is_command_allowed(command, allowed):
            return (
                "error: command not allowed (first token must be in allowlist); "
                f"allowed: {', '.join(sorted(allowed))}"
            )
        if not cfg.auto_approve_tools():
            if not confirm_run(command):
                return "user declined to run this command"
        root = t.tool_root()
        try:
            code, out, err = t.run_allowlisted_command(
                command, cwd=root, allowed=allowed
            )
        except t.ToolError as e:
            return f"error: {e}"
        parts = [f"exit {code}"]
        if out:
            parts.append(out.rstrip())
        if err:
            parts.append("stderr: " + err.rstrip())
        return "\n".join(parts)

    return f"error: unknown tool {name!r}"
