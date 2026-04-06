"""Placeholder for future OAuth/API mail integration."""

from __future__ import annotations

from waterloo.connectors.base import ContextConnector


class MailStubConnector(ContextConnector):
    """Reserved until a provider (Gmail, Microsoft) is implemented with OAuth2."""

    @property
    def title(self) -> str:
        return "mail"

    def is_configured(self) -> bool:
        return False

    def fetch_summary(self) -> str:
        return (
            "Mail connector is not implemented yet. A future version may add "
            "OAuth2 (Gmail or Microsoft) with least privilege. See README under "
            "Context connectors."
        )
