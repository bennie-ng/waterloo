"""Context connector protocol (calendar, mail, etc.)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ContextConnector(ABC):
    """Read-only context source for the REPL (no OAuth in base layer)."""

    @property
    @abstractmethod
    def title(self) -> str:
        """Short name for /help and panels."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether required env or files are present."""

    @abstractmethod
    def fetch_summary(self) -> str:
        """Human-readable block for the terminal (no secrets)."""
