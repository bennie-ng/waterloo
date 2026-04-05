"""Tests for memory recall (Given / When / Then style)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from waterloo.memory import (
    add_memory_note,
    connect,
    init_schema,
    recall_notes_for_query,
)


def test_given_notes_when_query_overlaps_then_recalls_relevant():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "t.db"
        conn = connect(db)
        init_schema(conn)
        add_memory_note(conn, "I prefer dark mode in all apps")
        add_memory_note(conn, "Unrelated: pineapple pizza opinions")
        recalled = recall_notes_for_query(conn, "Remind me about dark mode")
        assert any("dark" in r.lower() for r in recalled)
        assert not any("pizza" in r for r in recalled)
