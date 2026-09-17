"""Durable, privacy-preserving state and delta probes for Agent Rites."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class RiteStateError(ValueError):
    pass


def git_delta(previous: str | None, current: str) -> bool:
    return bool(current) and previous != current


class RiteState:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"last_sha": None, "last_success": None, "metrics": {}, "findings": [], "consecutive_failures": 0}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RiteStateError(str(exc)) from exc
        if not isinstance(data, dict) or not isinstance(data.get("metrics", {}), dict) or not isinstance(data.get("findings", []), list):
            raise RiteStateError("state must be a mapping with metrics and findings")
        return data

    def should_run(self, current_sha: str) -> bool:
        return git_delta(self.load().get("last_sha"), current_sha)

    def record(self, sha: str, *, success: bool, metrics: dict[str, Any], findings: list[str]) -> None:
        previous = self.load()
        data = {"last_sha": sha, "last_success": sha if success else previous.get("last_success"),
                "metrics": metrics, "findings": findings,
                "consecutive_failures": 0 if success else int(previous.get("consecutive_failures", 0)) + 1}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.path)
