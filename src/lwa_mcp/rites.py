"""Portable, fail-closed Agent Rite manifest contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class RiteManifestError(ValueError):
    pass


@dataclass(frozen=True)
class Trigger:
    kind: str
    cron: str | None = None


@dataclass(frozen=True)
class Workspace:
    mode: str = "worktree"
    base: str = "HEAD"


@dataclass(frozen=True)
class Agent:
    task: str = ""
    max_attempts: int = 1


@dataclass(frozen=True)
class RiteManifest:
    name: str
    trigger: Trigger
    workspace: Workspace
    agent: Agent
    hard_constraints: tuple[str, ...]
    objectives: tuple[str, ...]
    promotion_mode: str
    require_change: bool

    @classmethod
    def from_file(cls, path: str | Path) -> "RiteManifest":
        try:
            data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise RiteManifestError(str(exc)) from exc
        if not isinstance(data, dict) or data.get("version", 1) != 1 or not data.get("name"):
            raise RiteManifestError("version 1 and name are required")
        trigger = data.get("trigger") or {}
        if trigger.get("kind") not in {"cron", "event", "condition", "drift"}:
            raise RiteManifestError("trigger kind is invalid")
        workspace = data.get("workspace") or {}
        if workspace.get("mode", "worktree") not in {"worktree", "read-only"}:
            raise RiteManifestError("workspace mode is invalid")
        agent = data.get("agent") or {}
        attempts = agent.get("max_attempts", 1)
        if not isinstance(attempts, int) or not 1 <= attempts <= 10:
            raise RiteManifestError("max_attempts must be between 1 and 10")
        constraints = data.get("constraints") or {}
        promotion = data.get("promotion") or {}
        return cls(str(data["name"]), Trigger(trigger["kind"], trigger.get("cron")),
                   Workspace(workspace.get("mode", "worktree"), workspace.get("base", "HEAD")),
                   Agent(str(agent.get("task", "")), attempts), tuple(constraints.get("hard", ())),
                   tuple(constraints.get("objectives", data.get("objectives", ()))),
                   str(promotion.get("mode", "report")), bool(promotion.get("require_change", False)))
