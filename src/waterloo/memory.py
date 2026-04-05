"""SQLite persistence: transcripts and opt-in memory notes."""

from __future__ import annotations

import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_file: Path) -> sqlite3.Connection:
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );
        CREATE TABLE IF NOT EXISTS memory_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
        """
    )
    conn.commit()


def ensure_conversation(conn: sqlite3.Connection, conversation_id: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO conversations (id, created_at) VALUES (?, ?)",
        (conversation_id, _utc_now()),
    )
    conn.commit()


def append_message(conn: sqlite3.Connection, conversation_id: str, role: str, content: str) -> None:
    ensure_conversation(conn, conversation_id)
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (conversation_id, role, content, _utc_now()),
    )
    conn.commit()


def load_messages(conn: sqlite3.Connection, conversation_id: str, limit: int = 200) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        SELECT role, content FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
        LIMIT ?
        """,
        (conversation_id, limit),
    ).fetchall()
    return [{"role": str(r["role"]), "content": str(r["content"])} for r in rows]


def clear_messages(conn: sqlite3.Connection, conversation_id: str) -> None:
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    conn.commit()


def add_memory_note(conn: sqlite3.Connection, content: str) -> int:
    cur = conn.execute(
        "INSERT INTO memory_notes (content, created_at) VALUES (?, ?)",
        (content.strip(), _utc_now()),
    )
    conn.commit()
    return int(cur.lastrowid)


@dataclass(frozen=True)
class MemoryNote:
    id: int
    content: str


def list_memory_notes(conn: sqlite3.Connection) -> list[MemoryNote]:
    rows = conn.execute(
        "SELECT id, content FROM memory_notes ORDER BY id ASC",
    ).fetchall()
    return [MemoryNote(int(r["id"]), str(r["content"])) for r in rows]


def delete_memory_note(conn: sqlite3.Connection, note_id: int) -> bool:
    cur = conn.execute("DELETE FROM memory_notes WHERE id = ?", (note_id,))
    conn.commit()
    return cur.rowcount > 0


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {w for w in words if len(w) > 2}


def recall_notes_for_query(conn: sqlite3.Connection, user_text: str, max_notes: int = 8) -> list[str]:
    """Keyword overlap between user message and stored notes (no embeddings in v1)."""
    tokens = _tokenize(user_text)
    if not tokens:
        return []
    notes = list_memory_notes(conn)
    scored: list[tuple[int, MemoryNote]] = []
    for n in notes:
        nt = _tokenize(n.content)
        score = len(tokens & nt)
        if score > 0:
            scored.append((score, n))
    scored.sort(key=lambda x: (-x[0], x[1].id))
    return [n.content for _, n in scored[:max_notes]]


def new_conversation_id() -> str:
    return str(uuid.uuid4())
