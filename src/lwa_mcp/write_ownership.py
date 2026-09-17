"""Persistent, fail-closed file-scope ownership and delegation records."""

from __future__ import annotations

import fnmatch
import json
from datetime import UTC, datetime
from pathlib import Path


class OwnershipConflict(RuntimeError):
    """Raised when a write ownership rule cannot be granted or used."""


class OwnershipRegistry:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]\n", encoding="utf-8")

    def _records(self) -> list[dict[str, object]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def grant(self, task_id: str, actor: str, scopes: list[str], *, expires_at: str | None = None) -> None:
        if not scopes:
            raise OwnershipConflict("at least one write scope is required")
        records = self._records()
        for record in records:
            for existing in record["scopes"]:
                if any(fnmatch.fnmatchcase(scope, existing) or fnmatch.fnmatchcase(existing, scope)
                       for scope in scopes):
                    raise OwnershipConflict(f"ownership scope overlaps: {existing}")
        records.append({"kind": "ownership", "task_id": task_id, "actor": actor,
                        "scopes": scopes, "expires_at": expires_at, "revoked": False,
                        "granted_at": datetime.now(UTC).isoformat()})
        self.path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")

    def delegate(self, task_id: str, issuer: str, actor: str, scopes: list[str], *, expires_at: str | None = None) -> None:
        if not any(record["task_id"] == task_id and record["actor"] == issuer
                   and record.get("kind", "ownership") == "ownership"
                   and not record.get("revoked") and self._covers(record["scopes"], scopes)
                   for record in self._records()):
            raise OwnershipConflict(f"not authorized to delegate: {issuer}")
        records = self._records()
        for record in records:
            if record["task_id"] == task_id and record.get("kind", "ownership") == "ownership" and record["actor"] == issuer:
                continue
            if any(fnmatch.fnmatchcase(scope, existing) or fnmatch.fnmatchcase(existing, scope)
                   for existing in record["scopes"] for scope in scopes):
                raise OwnershipConflict(f"ownership scope overlaps: {record['scopes'][0]}")
        records.append({"kind": "delegation", "task_id": task_id, "issuer": issuer,
                        "actor": actor, "scopes": scopes, "expires_at": expires_at,
                        "revoked": False, "granted_at": datetime.now(UTC).isoformat()})
        self.path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")

    def revoke(self, task_id: str, delegate: str, *, actor: str) -> None:
        records = self._records()
        changed = False
        for record in records:
            if (record["task_id"] == task_id and record["kind"] == "delegation"
                    and record["actor"] == delegate):
                if not any(parent["task_id"] == task_id and parent["actor"] == actor
                           and parent.get("kind", "ownership") == "ownership" for parent in records):
                    raise OwnershipConflict(f"not authorized to revoke: {actor}")
                record["revoked"] = True
                changed = True
        if not changed:
            raise OwnershipConflict(f"delegation not found: {delegate}")
        self.path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")

    def authorize(self, task_id: str, actor: str, path: str) -> bool:
        now = datetime.now(UTC)
        for record in self._records():
            if record["task_id"] != task_id or record["actor"] != actor:
                continue
            if record.get("revoked"):
                raise OwnershipConflict(f"ownership grant revoked: {task_id}")
            expiry = record.get("expires_at")
            if expiry and datetime.fromisoformat(str(expiry)) <= now:
                raise OwnershipConflict(f"ownership grant expired: {task_id}")
            if any(fnmatch.fnmatchcase(path, scope) for scope in record["scopes"]):
                return True
        return False

    @staticmethod
    def _covers(parent_scopes: list[str], child_scopes: list[str]) -> bool:
        return all(any(fnmatch.fnmatchcase(scope, parent) for parent in parent_scopes)
                   for scope in child_scopes)
