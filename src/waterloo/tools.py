"""Guarded file read and shell execution (Phase 2 minimal tools)."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from waterloo import config as cfg


class ToolError(Exception):
    """User-facing tool failure."""


def tool_root() -> Path:
    """Directory boundary for /read and cwd for /run (see config.tool_root)."""
    return cfg.tool_root()


def max_read_bytes() -> int:
    try:
        return int(os.environ.get("WATERLOO_MAX_READ_BYTES", "262144"))
    except ValueError:
        return 262_144


def default_allowed_first_tokens() -> frozenset[str]:
    raw = os.environ.get(
        "WATERLOO_ALLOW_COMMANDS",
        "git,ls,pwd,which,echo,wc,head",
    )
    parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    return frozenset(parts)


def command_first_token(command: str) -> str:
    try:
        parts = shlex.split(command.strip())
    except ValueError as e:
        raise ToolError(f"invalid command quoting: {e}") from e
    if not parts:
        raise ToolError("empty command")
    return parts[0].lower()


def is_command_allowed(command: str, allowed: frozenset[str]) -> bool:
    return command_first_token(command) in allowed


def resolve_path_under_root(user_path: str, root: Path) -> Path:
    """Resolve a path and ensure it stays under root (after resolving)."""
    root = root.resolve()
    p = Path(user_path).expanduser()
    if not p.is_absolute():
        p = (root / p).resolve()
    else:
        p = p.resolve()
    try:
        p.relative_to(root)
    except ValueError as e:
        raise ToolError(f"path must stay under tool root {root}") from e
    return p


def read_text_file(path: Path, *, max_bytes: int) -> str:
    if not path.exists():
        raise ToolError(f"not found: {path}")
    if not path.is_file():
        raise ToolError(f"not a file: {path}")
    size = path.stat().st_size
    if size > max_bytes:
        raise ToolError(f"file too large ({size} bytes; max {max_bytes})")
    data = path.read_bytes()
    if len(data) > max_bytes:
        raise ToolError(f"file grew past max ({max_bytes} bytes)")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ToolError("file is not valid UTF-8") from e


def run_allowlisted_command(
    command: str,
    *,
    cwd: Path,
    allowed: frozenset[str],
    timeout: float = 60.0,
) -> tuple[int, str, str]:
    if not is_command_allowed(command, allowed):
        raise ToolError(
            f"command not allowed (first token must be one of: {', '.join(sorted(allowed))})"
        )
    try:
        argv = shlex.split(command)
    except ValueError as e:
        raise ToolError(f"invalid command: {e}") from e
    if not argv:
        raise ToolError("empty command")
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        raise ToolError(f"command timed out after {timeout}s") from None
    except OSError as e:
        raise ToolError(f"failed to run command: {e}") from e
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def tools_permitted_for_mode(mode: str, *, tools_local_only: bool) -> bool:
    """When tools_local_only is True, only local mode may use tools."""
    if not tools_local_only:
        return True
    return mode == "local"
