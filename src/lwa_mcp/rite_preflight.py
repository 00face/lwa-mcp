"""Deterministic recurrence preflight and bounded escalation selection."""

from __future__ import annotations


class RitePreflightError(ValueError):
    pass


def preflight(*, previous_sha: str | None, current_sha: str, findings: list[str], max_attempts: int = 3) -> dict[str, object]:
    if not current_sha or not isinstance(findings, list) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 10:
        raise RitePreflightError("invalid preflight inputs")
    if previous_sha == current_sha and not findings:
        return {"schema": "lwa-rite-preflight/v1", "decision": "skip", "level": 0, "max_attempts": 0}
    if not all(isinstance(item, str) and item for item in findings):
        raise RitePreflightError("findings must contain non-empty strings")
    text = " ".join(findings).lower()
    level = 3 if any(word in text for word in ("security", "vulnerability", "crash", "architecture")) else 2 if findings else 1
    return {"schema": "lwa-rite-preflight/v1", "decision": "run", "level": level,
            "max_attempts": min(max_attempts, max(1, level))}
