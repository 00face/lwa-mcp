"""Local, explainable policy for choosing consensus versus one route."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import TaskKind

_HIGH_RISK = re.compile(
    r"(?i)\b(security|vulnerab|credential|secret|auth|privacy|compliance|legal|medical|financial|"
    r"production|migration|destructive|delete|incident|exploit|regression|architecture|concurren)\b"
)
_ROUTINE_TASKS = {
    TaskKind.QUICK_RESPONSE,
    TaskKind.QUERY,
    TaskKind.CONVERSATION_COMPRESSION,
    TaskKind.TOKEN_OPTIMIZATION,
}


@dataclass(frozen=True, slots=True)
class ConsensusDecision:
    enabled: bool
    source: str
    reason: str
    risk: str
    override: bool | None

    def as_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "source": self.source,
            "reason": self.reason,
            "risk": self.risk,
            "override": self.override,
        }


def classify_prompt(task: TaskKind, prompt: str) -> tuple[str, str]:
    if task in {TaskKind.CODING_AUX, TaskKind.VERIFICATION, TaskKind.PLANNING}:
        return "high", f"{task.value} is a high-impact task"
    if _HIGH_RISK.search(prompt):
        return "high", "high-impact safety or change signal detected"
    if task in _ROUTINE_TASKS:
        return "routine", "routine task with no high-impact signal"
    return "moderate", "task is ambiguous; single-route is the economical default"


def decide(task: TaskKind, prompt: str, *, policy: str, override: bool | None) -> ConsensusDecision:
    if override is not None:
        return ConsensusDecision(override, "session_override", "explicit session toggle", "override", override)
    risk, reason = classify_prompt(task, prompt)
    if policy == "always":
        return ConsensusDecision(True, "configured", "consensus configured for every eligible prompt", risk, None)
    if policy == "off":
        return ConsensusDecision(False, "configured", "consensus disabled by configuration", risk, None)
    return ConsensusDecision(risk == "high", "adaptive", reason, risk, None)
