"""Small authoritative task ledger with SQLite-backed leases and audit events."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path


SCHEMA_VERSION = 1
_STATES = {"pending", "leased", "running", "blocked", "complete", "failed"}
_TRANSITIONS = {
    "pending": {"leased", "blocked", "failed"},
    "leased": {"running", "pending", "blocked", "failed"},
    "running": {"complete", "blocked", "failed"},
    "blocked": {"pending", "failed"},
    "failed": {"pending"},
    "complete": set(),
}


class LedgerConflict(RuntimeError):
    """Raised when a ledger operation would violate its concurrency contract."""


class TaskLedger:
    def __init__(self, path: str | Path, *, schema_version: int = SCHEMA_VERSION) -> None:
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema version: {schema_version}")
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY, description TEXT NOT NULL,
                    owner TEXT NOT NULL, state TEXT NOT NULL,
                    lease_owner TEXT, lease_until TEXT, controls_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                    actor TEXT NOT NULL, event TEXT NOT NULL, created_at TEXT NOT NULL
                );
                """
            )
            columns = {row[1] for row in db.execute("PRAGMA table_info(tasks)")}
            if "controls_json" not in columns:
                db.execute("ALTER TABLE tasks ADD COLUMN controls_json TEXT NOT NULL DEFAULT '{}'")
            row = db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
            if row is None:
                db.execute("INSERT INTO metadata VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
            elif int(row[0]) != SCHEMA_VERSION:
                raise ValueError(f"unsupported schema version: {row[0]}")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None, check_same_thread=False)
        db.row_factory = sqlite3.Row
        return db

    def create_task(self, task_id: str, description: str, *, owner: str) -> None:
        with self._connect() as db:
            try:
                db.execute(
                    "INSERT INTO tasks(task_id,description,owner,state) VALUES(?,?,?,'pending')",
                    (task_id, description, owner),
                )
                self._event(db, task_id, owner, "created")
            except sqlite3.IntegrityError as exc:
                raise LedgerConflict(f"task already exists: {task_id}") from exc

    def claim(self, task_id: str, actor: str, *, lease_seconds: int) -> bool:
        until = datetime.now(UTC) + timedelta(seconds=lease_seconds)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                raise LedgerConflict(f"task not found: {task_id}")
            if row["state"] != "pending":
                raise LedgerConflict(f"task {task_id} is already leased or not pending")
            db.execute(
                "UPDATE tasks SET state='leased', lease_owner=?, lease_until=? WHERE task_id=? AND state='pending'",
                (actor, until.isoformat(), task_id),
            )
            self._event(db, task_id, actor, "claimed")
            return True

    def transition(self, task_id: str, state: str, *, actor: str) -> None:
        if state not in _STATES:
            raise LedgerConflict(f"unknown state: {state}")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                raise LedgerConflict(f"task not found: {task_id}")
            if state not in _TRANSITIONS[row[0]]:
                raise LedgerConflict(f"invalid state transition: {row[0]} -> {state}")
            db.execute("UPDATE tasks SET state=? WHERE task_id=?", (state, task_id))
            self._event(db, task_id, actor, f"transition:{state}")

    def get(self, task_id: str) -> dict[str, str | None]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            raise LedgerConflict(f"task not found: {task_id}")
        result = dict(row)
        result["controls"] = json.loads(result.pop("controls_json"))
        return result

    def set_controls(self, task_id: str, controls: dict[str, str | int], *, actor: str) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM tasks WHERE task_id=?", (task_id,)).fetchone() is None:
                raise LedgerConflict(f"task not found: {task_id}")
            db.execute("UPDATE tasks SET controls_json=? WHERE task_id=?", (json.dumps(controls), task_id))
            self._event(db, task_id, actor, "controls_updated")

    def events(self, task_id: str) -> list[dict[str, str]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM events WHERE task_id=? ORDER BY event_id", (task_id,)).fetchall()
        return [dict(row) for row in rows]

    def stop(self, task_id: str, reason: str, *, actor: str) -> None:
        if not reason:
            raise ValueError("stop reason is required")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                raise LedgerConflict(f"task not found: {task_id}")
            if row[0] == "blocked":
                return
            if row[0] not in {"leased", "running", "pending"}:
                raise LedgerConflict(f"cannot stop task in state: {row[0]}")
            db.execute("UPDATE tasks SET state='blocked', lease_owner=NULL, lease_until=NULL WHERE task_id=?", (task_id,))
            self._event(db, task_id, actor, f"stopped:{reason}")

    @staticmethod
    def _event(db: sqlite3.Connection, task_id: str, actor: str, event: str) -> None:
        db.execute(
            "INSERT INTO events(task_id,actor,event,created_at) VALUES(?,?,?,?)",
            (task_id, actor, event, datetime.now(UTC).isoformat()),
        )
