"""Read-only calendar via local .ics file or HTTPS URL."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
from icalendar import Calendar

from waterloo.connectors.base import ContextConnector
from waterloo.logging_utils import redact_secrets

log = logging.getLogger("waterloo")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_start(raw: date | datetime) -> datetime:
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=timezone.utc)
        return raw.astimezone(timezone.utc)
    return datetime.combine(raw, datetime.min.time(), tzinfo=timezone.utc)


def upcoming_events_from_ics(
    ics_bytes: bytes,
    *,
    now: datetime | None = None,
    days: int = 14,
    max_events: int = 20,
) -> list[tuple[datetime, str, bool]]:
    """
    Return upcoming VEVENTs in [now, now+days], sorted by start.

    Each item is (start_utc, summary, is_all_day).

    Skips VEVENTs with RRULE (recurrence not expanded in this version).
    """
    now = now or _utc_now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)
    end = now + timedelta(days=days)

    cal = Calendar.from_ical(ics_bytes)
    out: list[tuple[datetime, str, bool]] = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        if component.get("rrule") is not None:
            continue
        dtstart = component.get("dtstart")
        if dtstart is None:
            continue
        raw = dtstart.dt
        is_all_day = isinstance(raw, date) and not isinstance(raw, datetime)
        start = _normalize_start(raw)
        if start < now or start > end:
            continue
        summ = component.get("summary")
        title = str(summ) if summ is not None else "(no title)"
        out.append((start, title.strip(), is_all_day))

    out.sort(key=lambda x: x[0])
    return out[:max_events]


def format_events_lines(events: list[tuple[datetime, str, bool]]) -> str:
    if not events:
        return "No upcoming events in the configured window."
    lines: list[str] = []
    for start, title, all_day in events:
        if all_day:
            lines.append(f"{start.date()}  {title}")
        else:
            lines.append(f"{start.strftime('%Y-%m-%d %H:%M')} UTC  {title}")
    return "\n".join(lines)


class IcsCalendarConnector(ContextConnector):
    """Load ICS from WATERLOO_ICAL_PATH or WATERLOO_ICAL_URL."""

    @property
    def title(self) -> str:
        return "calendar"

    def is_configured(self) -> bool:
        from waterloo import config as cfg

        return bool(cfg.ical_path() or cfg.ical_url())

    def fetch_summary(self) -> str:
        from waterloo import config as cfg

        path = cfg.ical_path()
        url = cfg.ical_url()
        if not path and not url:
            return (
                "Calendar not configured. Set WATERLOO_ICAL_PATH (local .ics file) "
                "or WATERLOO_ICAL_URL (HTTPS)."
            )
        try:
            data = _load_ics_bytes(path, url, timeout=cfg.ical_fetch_timeout())
        except Exception as e:
            msg = redact_secrets(str(e))
            log.info("Calendar fetch failed: %s", msg)
            return f"Calendar error: {msg}"

        events = upcoming_events_from_ics(data)
        return format_events_lines(events)


def _load_ics_bytes(
    path: str | None,
    url: str | None,
    *,
    timeout: float,
) -> bytes:
    if path:
        p = Path(path).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"ICS file not found: {p}")
        return p.read_bytes()
    if url:
        u = url.strip()
        if not u.lower().startswith("https://"):
            raise ValueError("WATERLOO_ICAL_URL must use https://")
        with httpx.Client(timeout=timeout) as client:
            r = client.get(u)
            r.raise_for_status()
            return r.content
    raise ValueError("no ICS path or URL")
