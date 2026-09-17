"""Explainable pre-flight routing for routine versus complex work."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EffortDecision:
    tier: str
    confidence: float
    reason: str
    explicit: bool


_COMPLEX = re.compile(
    r"(?i)\b(debug|race|concurren|protocol|opcode|migration|security|regression|architecture|refactor|crash|corrupt)"
)
_ROUTINE = re.compile(r"(?i)\b(rename|typo|format|css|readme|docs?|comment|bump|lint|simple|small)\b")


def choose_effort(prompt: str, recent_diff: str = "", explicit: str | None = None) -> EffortDecision:
    """Choose an effort tier from local text signals without external calls."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")
    if explicit is not None:
        if explicit not in {"routine", "complex"}:
            raise ValueError("explicit effort must be routine or complex")
        return EffortDecision(explicit, 1.0, "explicit operator selection", True)
    material = f"{prompt}\n{recent_diff}"
    complex_hits = len(_COMPLEX.findall(material))
    routine_hits = len(_ROUTINE.findall(material))
    if complex_hits > routine_hits:
        return EffortDecision("complex", min(1.0, 0.6 + complex_hits * 0.1), "complexity signals detected", False)
    if routine_hits and not complex_hits:
        return EffortDecision("routine", min(1.0, 0.6 + routine_hits * 0.1), "routine-change signals detected", False)
    return EffortDecision("complex", 0.5, "ambiguous request; conservative default", False)


def resolve_reasoning_effort(
    prompt: str, recent_diff: str = "", explicit: str | None = None
) -> tuple[str, EffortDecision]:
    """Map the router decision to Lwa's canonical provider effort values."""
    decision = choose_effort(prompt, recent_diff, explicit)
    return ("instant" if decision.tier == "routine" else "high"), decision
