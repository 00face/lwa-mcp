"""Durable, Lwa-owned terminal sessions and chat messages."""

from __future__ import annotations

import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .config import STATE_DIR


@dataclass(frozen=True)
class LwaMessage:
    session_id: str
    role: str
    content: str
    created_at: str


class LwaHistory:
    """Small SQLite repository deliberately separate from router telemetry."""

    def __init__(self, path: Path | None = None, *, max_messages: int = 400) -> None:
        self.path = path or Path(os.environ.get("LWA_SESSION_DB", STATE_DIR / "sessions.sqlite3"))
        self.max_messages = max(1, max_messages)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS lwa_sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS lwa_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES lwa_sessions(session_id),
                    role TEXT NOT NULL CHECK(role IN ('system', 'user', 'assistant', 'error')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_lwa_messages_session
                    ON lwa_messages(session_id, id);
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def create_session(self, session_id: str | None = None) -> str:
        session_id = session_id or f"lwa-{uuid.uuid4().hex}"
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO lwa_sessions(session_id, created_at, updated_at) VALUES (?, ?, ?)",
                (session_id, now, now),
            )
        return session_id

    def ensure_session(self, session_id: str | None = None) -> str:
        if session_id:
            with self._connect() as connection:
                exists = connection.execute(
                    "SELECT 1 FROM lwa_sessions WHERE session_id = ?", (session_id,)
                ).fetchone()
            if exists:
                return session_id
        return self.create_session(session_id)

    def append(self, session_id: str, role: str, content: str) -> LwaMessage:
        if role not in {"system", "user", "assistant", "error"}:
            raise ValueError(f"unsupported Lwa message role: {role}")
        content = str(content).strip()
        if not content:
            raise ValueError("Lwa history cannot store empty content")
        session_id = self.ensure_session(session_id)
        created_at = self._now()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO lwa_messages(session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (session_id, role, content, created_at),
            )
            connection.execute(
                "UPDATE lwa_sessions SET updated_at = ? WHERE session_id = ?",
                (created_at, session_id),
            )
            overflow = connection.execute(
                "SELECT id FROM lwa_messages WHERE session_id = ? ORDER BY id DESC LIMIT -1 OFFSET ?",
                (session_id, self.max_messages),
            ).fetchall()
            if overflow:
                connection.executemany(
                    "DELETE FROM lwa_messages WHERE id = ?",
                    ((row["id"],) for row in overflow),
                )
        return LwaMessage(session_id, role, content, created_at)

    def messages(self, session_id: str) -> list[LwaMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT session_id, role, content, created_at FROM lwa_messages WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
        return [
            LwaMessage(row["session_id"], row["role"], row["content"], row["created_at"])
            for row in rows
        ]

    def sessions(self, limit: int = 20) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT session_id FROM lwa_sessions ORDER BY updated_at DESC LIMIT ?",
                (max(1, limit),),
            ).fetchall()
        return [str(row["session_id"]) for row in rows]
