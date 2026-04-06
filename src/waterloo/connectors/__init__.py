"""Context connectors (calendar ICS, mail stub, ...)."""

from waterloo.connectors.base import ContextConnector
from waterloo.connectors.calendar_ics import IcsCalendarConnector, upcoming_events_from_ics
from waterloo.connectors.mail_stub import MailStubConnector

__all__ = [
    "ContextConnector",
    "IcsCalendarConnector",
    "MailStubConnector",
    "upcoming_events_from_ics",
]
