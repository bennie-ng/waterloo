"""Paths and environment-driven settings."""

from __future__ import annotations

import os
from pathlib import Path


def workspace_root() -> Path:
    """
    Single workspace root (defaults to ~/.waterloo).

    Override with WATERLOO_WORKSPACE. Subdirectories: data/, sandbox/, ical/.
    """
    raw = os.environ.get("WATERLOO_WORKSPACE", "").strip()
    if raw:
        root = Path(raw).expanduser().resolve()
    else:
        root = (Path.home() / ".waterloo").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def data_dir() -> Path:
    """SQLite and app data: WATERLOO_DATA_DIR or <workspace>/data."""
    override = os.environ.get("WATERLOO_DATA_DIR", "").strip()
    if override:
        p = Path(override).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p
    d = workspace_root() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d.resolve()


def db_path() -> Path:
    return data_dir() / "waterloo.db"


def tool_root() -> Path:
    """Sandbox for /read and /run: WATERLOO_TOOL_ROOT or <workspace>/sandbox."""
    override = os.environ.get("WATERLOO_TOOL_ROOT", "").strip()
    if override:
        p = Path(override).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p
    s = workspace_root() / "sandbox"
    s.mkdir(parents=True, exist_ok=True)
    return s.resolve()


def ical_path() -> str | None:
    """Explicit WATERLOO_ICAL_PATH override (any path on disk)."""
    p = os.environ.get("WATERLOO_ICAL_PATH", "").strip()
    return p if p else None


def default_ical_file() -> Path:
    """Default location for calendar.ics: <workspace>/ical/calendar.ics (dir created)."""
    ical_dir = workspace_root() / "ical"
    ical_dir.mkdir(parents=True, exist_ok=True)
    return (ical_dir / "calendar.ics").resolve()


def resolved_local_ics_path() -> Path | None:
    """
    Local .ics file to use: env path if set, else default file if it exists.
    """
    if p := ical_path():
        return Path(p).expanduser().resolve()
    default = default_ical_file()
    if default.is_file():
        return default
    return None


def ollama_base() -> str:
    return os.environ.get("WATERLOO_OLLAMA_BASE", "http://127.0.0.1:11434").rstrip("/")


def ollama_model() -> str:
    return os.environ.get("WATERLOO_OLLAMA_MODEL", "llama3.2")


def openai_base_url() -> str:
    return os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")


def openai_model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def openai_api_key() -> str | None:
    key = os.environ.get("OPENAI_API_KEY")
    return key if key else None


def initial_mode() -> str:
    m = os.environ.get("WATERLOO_MODE", "local").lower().strip()
    if m in {"auto", "local", "cloud"}:
        return m
    return "local"


def fallback_cloud_enabled() -> bool:
    return os.environ.get("WATERLOO_FALLBACK_CLOUD", "0").strip() in {"1", "true", "yes"}


def tools_local_only() -> bool:
    """When True, /read and /run are only available in local routing mode."""
    return os.environ.get("WATERLOO_TOOLS_LOCAL_ONLY", "1").strip() in {"1", "true", "yes"}


def auto_approve_tools() -> bool:
    """When True, skip the y/n prompt before /run."""
    return os.environ.get("WATERLOO_AUTO_APPROVE_TOOLS", "0").strip() in {"1", "true", "yes"}


def llm_tools_enabled() -> bool:
    """When False, LLM tool loop is disabled (plain chat only). Default on."""
    v = os.environ.get("WATERLOO_LLM_TOOLS", "1").strip().lower()
    return v not in {"0", "false", "no", "off"}


def agent_max_steps() -> int:
    try:
        return max(1, int(os.environ.get("WATERLOO_AGENT_MAX_STEPS", "8")))
    except ValueError:
        return 8


def ical_url() -> str | None:
    u = os.environ.get("WATERLOO_ICAL_URL", "").strip()
    return u if u else None


def ical_fetch_timeout() -> float:
    try:
        return float(os.environ.get("WATERLOO_ICAL_TIMEOUT", "30"))
    except ValueError:
        return 30.0
