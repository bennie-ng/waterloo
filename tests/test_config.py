"""Config defaults (Given / When / Then style)."""

from __future__ import annotations

from waterloo import config as cfg
from waterloo.config import initial_mode


def test_given_no_waterloo_mode_env_when_initial_mode_then_local(monkeypatch):
    monkeypatch.delenv("WATERLOO_MODE", raising=False)
    assert initial_mode() == "local"


def test_given_home_patched_when_workspace_root_then_waterloo_under_home(monkeypatch, tmp_path):
    monkeypatch.delenv("WATERLOO_WORKSPACE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert cfg.workspace_root() == (tmp_path / ".waterloo").resolve()


def test_given_waterloo_workspace_env_when_workspace_root_then_that_path(monkeypatch, tmp_path):
    ws = tmp_path / "myws"
    monkeypatch.setenv("WATERLOO_WORKSPACE", str(ws))
    assert cfg.workspace_root() == ws.resolve()


def test_given_no_data_dir_override_when_data_dir_then_workspace_data(monkeypatch, tmp_path):
    monkeypatch.delenv("WATERLOO_DATA_DIR", raising=False)
    monkeypatch.delenv("WATERLOO_WORKSPACE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert cfg.data_dir() == (tmp_path / ".waterloo" / "data").resolve()


def test_given_data_dir_override_when_data_dir_then_override(monkeypatch, tmp_path):
    d = tmp_path / "custom_data"
    monkeypatch.setenv("WATERLOO_DATA_DIR", str(d))
    assert cfg.data_dir() == d.resolve()
