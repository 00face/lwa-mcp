"""Fail-closed promotion and rollback decision boundary."""

from __future__ import annotations

from typing import Any


def decide_promotion(*, verifier: dict[str, Any], changed_files: int, approved: bool, require_change: bool) -> dict[str, Any]:
    blockers: list[str] = []
    if verifier.get("promote") is not True or verifier.get("failures"):
        blockers.append("verifier_failed")
    if not approved:
        blockers.append("approval_required")
    if require_change and changed_files < 1:
        blockers.append("change_required")
    return {"schema": "lwa-promotion/v1", "status": "ready" if not blockers else "blocked",
            "blockers": blockers, "rollback": not bool(blockers), "promoted": False,
            "changed_files": changed_files}
