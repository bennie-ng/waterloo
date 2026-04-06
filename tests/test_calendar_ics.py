"""Tests for ICS calendar connector (Given / When / Then style)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from waterloo.connectors.calendar_ics import IcsCalendarConnector, upcoming_events_from_ics
from waterloo.connectors.mail_stub import MailStubConnector


def _ics_with_event_at(dt_utc: datetime, summary: str = "Meet") -> bytes:
    s = dt_utc.strftime("%Y%m%dT%H%M%SZ")
    raw = f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:evt1
DTSTART:{s}
SUMMARY:{summary}
END:VEVENT
END:VCALENDAR
"""
    return raw.encode("utf-8")


def test_given_future_event_when_parse_then_included():
    now = datetime(2030, 1, 1, 12, 0, tzinfo=timezone.utc)
    ev = now + timedelta(days=3)
    data = _ics_with_event_at(ev, "Alpha")
    events = upcoming_events_from_ics(data, now=now, days=14, max_events=20)
    assert len(events) == 1
    assert events[0][1] == "Alpha"


def test_given_rrule_event_when_parse_then_skipped():
    now = datetime(2030, 1, 1, 12, 0, tzinfo=timezone.utc)
    raw = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:r
DTSTART:20300105T120000Z
RRULE:FREQ=DAILY
SUMMARY:Recur
END:VEVENT
END:VCALENDAR
"""
    events = upcoming_events_from_ics(raw, now=now, days=30, max_events=20)
    assert events == []


def test_given_ics_file_when_connector_fetch_summary_then_shows_title(monkeypatch, tmp_path):
    now = datetime.now(timezone.utc)
    ev = now + timedelta(days=5)
    data = _ics_with_event_at(ev, "FileEvent")
    p = tmp_path / "cal.ics"
    p.write_bytes(data)
    monkeypatch.setenv("WATERLOO_ICAL_PATH", str(p))
    monkeypatch.delenv("WATERLOO_ICAL_URL", raising=False)
    c = IcsCalendarConnector()
    assert c.is_configured() is True
    out = c.fetch_summary()
    assert "FileEvent" in out


def test_given_default_workspace_calendar_when_no_ical_env_then_configured_and_summary(
    monkeypatch, tmp_path
):
    """Given calendar.ics under ~/.waterloo/ical with no WATERLOO_ICAL_* env, when fetch, then event shows."""
    now = datetime.now(timezone.utc)
    ev = now + timedelta(days=5)
    data = _ics_with_event_at(ev, "WorkspaceDefault")
    ical_dir = tmp_path / ".waterloo" / "ical"
    ical_dir.mkdir(parents=True)
    (ical_dir / "calendar.ics").write_bytes(data)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("WATERLOO_WORKSPACE", raising=False)
    monkeypatch.delenv("WATERLOO_ICAL_PATH", raising=False)
    monkeypatch.delenv("WATERLOO_ICAL_URL", raising=False)
    c = IcsCalendarConnector()
    assert c.is_configured() is True
    out = c.fetch_summary()
    assert "WorkspaceDefault" in out


def test_given_mail_stub_when_fetch_summary_then_not_configured():
    m = MailStubConnector()
    assert m.is_configured() is False
    assert "not implemented" in m.fetch_summary().lower()
