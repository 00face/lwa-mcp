"""Operator-controlled markdown session memory under a repository root."""

from __future__ import annotations

import re
import shutil
from datetime import UTC, date, datetime
from pathlib import Path


def _root(repo_path: str | Path) -> Path:
    """Resolve a repository and reject non-directory roots."""
    root = Path(repo_path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"repository path is not a directory: {repo_path}")
    return root


def _memory_dir(repo_path: str | Path) -> Path:
    return _root(repo_path) / ".agent-mem"


def sync_write_session(repo_path: str | Path, agent_name: str, summary: str, decisions: list[str] | None = None, open_items: list[str] | None = None, *, session_date: date | None = None) -> Path:
    """Append one agent/day session record and refresh the small index."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", agent_name):
        raise ValueError("agent_name must contain only letters, numbers, '_' or '-'")
    if not summary.strip():
        raise ValueError("summary must be non-empty")
    memory = _memory_dir(repo_path)
    sessions = memory / "sessions"
    sessions.mkdir(mode=0o700, parents=True, exist_ok=True)
    target_date = session_date or datetime.now(UTC).date()
    target = sessions / f"{target_date.isoformat()}-{agent_name}.md"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## Session {agent_name}\n\n{summary.strip()}\n")
        if decisions:
            handle.write("\n### Decisions\n" + "\n".join(f"- {item}" for item in decisions) + "\n")
        if open_items:
            handle.write("\n### Open items\n" + "\n".join(f"- {item}" for item in open_items) + "\n")
    (memory / "INDEX.md").write_text(_build_index(memory), encoding="utf-8")
    return target


def _build_index(memory: Path) -> str:
    files = sorted((memory / "sessions").glob("*.md")) if (memory / "sessions").is_dir() else []
    rows = ["# Agent memory index", "", "| Session | File |", "|---|---|"]
    rows.extend(f"| {path.stem} | `sessions/{path.name}` |" for path in files)
    return "\n".join(rows) + "\n"


def sync_read_briefing(repo_path: str | Path, *, tail_lines: int = 80) -> str:
    """Return index, overview, and a bounded tail of the newest session."""
    if not 1 <= tail_lines <= 500:
        raise ValueError("tail_lines must be between 1 and 500")
    memory = _memory_dir(repo_path)
    parts = [
        (memory / filename).read_text(encoding="utf-8")
        for filename in ("INDEX.md", "PROJECT_OVERVIEW.md")
        if (memory / filename).is_file()
    ]
    sessions = sorted((memory / "sessions").glob("*.md")) if (memory / "sessions").is_dir() else []
    if sessions:
        parts.append("\n".join(sessions[-1].read_text(encoding="utf-8").splitlines()[-tail_lines:]))
    return "\n\n".join(parts)


def sync_rotate(repo_path: str | Path, keep_recent_n: int = 10, *, dry_run: bool = False) -> int:
    """Move older sessions to warm archive, or count them without mutation."""
    if keep_recent_n < 0:
        raise ValueError("keep_recent_n must not be negative")
    memory = _memory_dir(repo_path)
    sessions = sorted((memory / "sessions").glob("*.md")) if (memory / "sessions").is_dir() else []
    archive = memory / "archive" / "warm"
    rotated = sessions[:-keep_recent_n] if keep_recent_n else sessions
    if not dry_run:
        archive.mkdir(mode=0o700, parents=True, exist_ok=True)
        for path in rotated:
            shutil.move(str(path), archive / path.name)
    if rotated and not dry_run:
        (memory / "INDEX.md").write_text(_build_index(memory), encoding="utf-8")
    return len(rotated)
