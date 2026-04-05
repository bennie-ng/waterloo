"""Tests for log redaction (Given / When / Then style)."""

from __future__ import annotations

from waterloo.logging_utils import redact_secrets


def test_given_openai_style_key_when_redact_then_masked():
    text = "error sk-abcdefghijklmnopqrstuvwxyz0123456789abcd token"
    out = redact_secrets(text)
    assert "sk-" not in out or "***" in out
    assert "abcdefghijklmnopqrstuvwxyz0123456789abcd" not in out


def test_given_bearer_token_when_redact_then_masked():
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    out = redact_secrets(text)
    assert "Bearer ***" in out or "***" in out
