"""Safe logging helpers (redact secrets from diagnostic strings)."""

from __future__ import annotations

import re

_SK_OPENAI = re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b")
_BEARER = re.compile(r"\bBearer\s+[A-Za-z0-9._-]+\b", re.IGNORECASE)
_HEX_LONG = re.compile(r"\b[0-9a-fA-F]{32,}\b")


def redact_secrets(text: str) -> str:
    """Redact common secret patterns from log or debug output."""
    if not text:
        return text
    out = _SK_OPENAI.sub("sk-***", text)
    out = _BEARER.sub("Bearer ***", out)
    out = _HEX_LONG.sub("***", out)
    return out
