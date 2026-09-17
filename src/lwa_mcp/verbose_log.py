"""Opt-in sensitive JSONL tracing for the Lwa terminal surface."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import STATE_DIR


class VerboseTrace:
    """Write terminal inputs and visible Codex events to mode-0600 JSONL."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path) if path else STATE_DIR / "verbose-terminal.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self.path.chmod(0o600)
        self.record(
            "lwa",
            "meta",
            "trace_started",
            {"sensitive": True, "warning": "contains prompts, commands, and responses"},
        )

    def record(self, source: str, direction: str, kind: str, payload: Any) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "source": source,
            "direction": direction,
            "kind": kind,
            "payload": payload,
        }
        try:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(record, ensure_ascii=False, separators=(",", ":"), default=str)
                    + "\n"
                )
            self.path.chmod(0o600)
        except OSError:
            return

    def close(self) -> None:
        self.record("lwa", "meta", "trace_stopped", {})
