"""Config defaults (Given / When / Then style)."""

from __future__ import annotations

from waterloo.config import initial_mode


def test_given_no_waterloo_mode_env_when_initial_mode_then_local(monkeypatch):
    monkeypatch.delenv("WATERLOO_MODE", raising=False)
    assert initial_mode() == "local"
