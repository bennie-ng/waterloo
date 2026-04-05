"""Paths and environment-driven settings."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def default_data_dir() -> Path:
    """User-writable data directory (macOS Application Support, else XDG-style)."""
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "waterloo"
    return home / ".local" / "share" / "waterloo"


def data_dir() -> Path:
    override = os.environ.get("WATERLOO_DATA_DIR")
    if override:
        return Path(override).expanduser()
    return default_data_dir()


def db_path() -> Path:
    return data_dir() / "waterloo.db"


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
    m = os.environ.get("WATERLOO_MODE", "auto").lower().strip()
    if m in {"auto", "local", "cloud"}:
        return m
    return "auto"


def fallback_cloud_enabled() -> bool:
    return os.environ.get("WATERLOO_FALLBACK_CLOUD", "0").strip() in {"1", "true", "yes"}
