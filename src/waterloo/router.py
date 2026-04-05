"""Hybrid routing: local vs cloud based on mode and simple sensitivity rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Mode = Literal["auto", "local", "cloud"]

# Substrings in user text (lowercased) that bias `auto` toward local.
_SENSITIVE_SUBSTRINGS: tuple[str, ...] = (
    "password",
    "secret",
    "api key",
    "private key",
    "ssn",
    "social security",
    "credit card",
    "passphrase",
)


def looks_sensitive(user_text: str) -> bool:
    """Heuristic: treat certain phrases as sensitive for routing in auto mode."""
    lower = user_text.lower()
    return any(s in lower for s in _SENSITIVE_SUBSTRINGS)


@dataclass(frozen=True)
class RouteDecision:
    """Which backend to use and optional human-readable reason."""

    backend: Literal["local", "cloud"]
    reason: str


def decide_route(
    mode: Mode,
    user_text: str,
    *,
    local_available: bool,
    cloud_available: bool,
    fallback_cloud: bool,
) -> RouteDecision:
    """
    Choose local vs cloud.

    - local: force Ollama when possible; optional fallback to cloud.
    - cloud: force cloud when possible.
    - auto: sensitive -> local if available else cloud if fallback else cloud if available;
            non-sensitive -> cloud if available else local.
    """
    if mode == "local":
        if local_available:
            return RouteDecision("local", "mode=local")
        if fallback_cloud and cloud_available:
            return RouteDecision("cloud", "mode=local but local unavailable; fallback to cloud")
        if cloud_available:
            return RouteDecision("cloud", "mode=local but local unavailable; using cloud")
        return RouteDecision("local", "mode=local but no providers available")

    if mode == "cloud":
        if cloud_available:
            return RouteDecision("cloud", "mode=cloud")
        if local_available:
            return RouteDecision("local", "mode=cloud but cloud unavailable; using local")
        return RouteDecision("cloud", "mode=cloud but no providers available")

    # auto
    sensitive = looks_sensitive(user_text)
    if sensitive:
        if local_available:
            return RouteDecision("local", "auto: sensitive content -> local")
        if fallback_cloud and cloud_available:
            return RouteDecision("cloud", "auto: sensitive but local down; fallback to cloud")
        if cloud_available:
            return RouteDecision("cloud", "auto: sensitive but local unavailable")
        return RouteDecision("local", "auto: sensitive; no cloud")

    if cloud_available:
        return RouteDecision("cloud", "auto: default -> cloud")
    if local_available:
        return RouteDecision("local", "auto: cloud unavailable -> local")
    return RouteDecision("cloud", "auto: no providers available")
