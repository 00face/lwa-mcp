"""Conservative snapshot and active-context slicing for markdown ledgers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_PHASE = re.compile(r"^#{1,6}\s+Phase\s+(\d+)\b", re.IGNORECASE)
_DEPENDENCY = re.compile(r"^\s*(?:[-*]\s*)?Depends on:\s*(.+)$", re.IGNORECASE)


@dataclass(frozen=True)
class LedgerSlice:
    active_phase: str
    sections: tuple[str, ...]
    changed: bool
    fingerprint: str


def _sections(ledger: str) -> dict[str, str]:
    found: dict[str, list[str]] = {}
    current: str | None = None
    for line in ledger.splitlines():
        match = _PHASE.match(line)
        if match:
            current = f"Phase {int(match.group(1))}"
            found.setdefault(current, []).append(line)
        elif current is not None:
            found[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in found.items()}


def slice_ledger(ledger: str, active_phase: str, previous_fingerprint: str | None = None) -> LedgerSlice:
    """Return the active phase and explicitly declared immediate dependencies."""
    if not isinstance(ledger, str) or not ledger.strip():
        raise ValueError("ledger must be non-empty text")
    sections = _sections(ledger)
    normalized = active_phase.strip().title()
    if not normalized.startswith("Phase ") or normalized not in sections:
        raise ValueError(f"active phase {active_phase!r} is missing from ledger")
    dependency_map: dict[str, tuple[str, ...]] = {}
    for name, section in sections.items():
        dependencies: list[str] = []
        for line in section.splitlines():
            match = _DEPENDENCY.match(line)
            if match:
                dependencies.extend(part.strip().title() for part in match.group(1).split(","))
        dependency_map[name] = tuple(dict.fromkeys(dependencies))
    dependencies = list(dependency_map[normalized])
    missing = [dependency for dependency in dependencies if dependency not in sections]
    if missing:
        raise ValueError(f"ledger dependencies missing: {', '.join(missing)}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise ValueError(f"ledger dependency cycle detected at {name}")
        if name in visited:
            return
        visiting.add(name)
        for dependency in dependency_map[name]:
            if dependency not in sections:
                raise ValueError(f"ledger dependencies missing: {dependency}")
            visit(dependency)
        visiting.remove(name)
        visited.add(name)

    visit(normalized)
    selected = tuple(dict.fromkeys([normalized, *dependencies]))
    fingerprint = hashlib.sha256(ledger.encode("utf-8")).hexdigest()
    return LedgerSlice(normalized, tuple(sections[name] for name in selected), fingerprint != previous_fingerprint, fingerprint)
