"""Tests for hybrid routing (Given / When / Then style)."""

from __future__ import annotations

from waterloo.router import decide_route, looks_sensitive


def test_given_auto_non_sensitive_when_cloud_available_then_uses_cloud():
    d = decide_route(
        "auto",
        "What is 2+2?",
        local_available=True,
        cloud_available=True,
        fallback_cloud=False,
    )
    assert d.backend == "cloud"
    assert "cloud" in d.reason.lower()


def test_given_auto_sensitive_when_local_available_then_uses_local():
    d = decide_route(
        "auto",
        "My api key is secret",
        local_available=True,
        cloud_available=True,
        fallback_cloud=False,
    )
    assert d.backend == "local"


def test_given_auto_sensitive_when_local_down_and_fallback_then_uses_cloud():
    d = decide_route(
        "auto",
        "password=foo",
        local_available=False,
        cloud_available=True,
        fallback_cloud=True,
    )
    assert d.backend == "cloud"


def test_given_mode_local_when_local_available_then_local():
    d = decide_route(
        "local",
        "anything",
        local_available=True,
        cloud_available=True,
        fallback_cloud=False,
    )
    assert d.backend == "local"


def test_given_mode_cloud_when_cloud_available_then_cloud():
    d = decide_route(
        "cloud",
        "anything",
        local_available=True,
        cloud_available=True,
        fallback_cloud=False,
    )
    assert d.backend == "cloud"


def test_given_mode_cloud_when_cloud_unavailable_then_falls_back_to_local():
    d = decide_route(
        "cloud",
        "anything",
        local_available=True,
        cloud_available=False,
        fallback_cloud=False,
    )
    assert d.backend == "local"


def test_looks_sensitive_detects_api_key_phrase():
    assert looks_sensitive("here is my api key") is True


def test_looks_sensitive_plain_question_false():
    assert looks_sensitive("What is the capital of France?") is False
