"""Manifest-driven, managed-block synchronization for project AGENTS files."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

START = "<!-- lwa-mcp:managed:start -->"
END = "<!-- lwa-mcp:managed:end -->"


@dataclass(frozen=True)
class SyncChange:
    path: Path
    changed: bool
    content: str


def _managed_block(shared: str, delta: str = "") -> str:
    body = "\n".join(line.rstrip() for line in (shared.strip(), delta.strip()) if line.strip())
    return f"{START}\n{body}\n{END}"


def render_agents(existing: str, shared: str, delta: str = "") -> str:
    """Replace exactly one managed block while preserving unmanaged guidance."""
    if START in existing and END not in existing:
        raise ValueError("AGENTS.md has an unterminated managed block")
    block = _managed_block(shared, delta)
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if pattern.search(existing):
        return pattern.sub(block, existing, count=1)
    return existing.rstrip() + "\n\n" + block + "\n"


def validate_manifest(manifest: dict) -> None:
    """Reject malformed or conflicting project manifests before any write."""
    if not isinstance(manifest, dict) or not isinstance(manifest.get("shared"), str) or not manifest["shared"].strip():
        raise ValueError("manifest requires non-empty shared guidance")
    if START in manifest["shared"] or END in manifest["shared"]:
        raise ValueError("shared guidance must not contain managed markers")
    projects = manifest.get("projects")
    if not isinstance(projects, list):
        raise TypeError("manifest projects must be a list")
    seen: set[Path] = set()
    for entry in projects:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise TypeError("each project requires a path")
        path = Path(entry["path"]).expanduser()
        if path in seen:
            raise ValueError(f"duplicate project path: {path}")
        seen.add(path)
        delta = entry.get("delta", "")
        if not isinstance(delta, str) or START in delta or END in delta:
            raise ValueError(f"invalid managed markers in project delta: {path}")


def synchronize(manifest: dict, *, apply: bool = False, backup_dir: str | Path | None = None) -> tuple[SyncChange, ...]:
    """Plan or apply synchronization for manifest entries; default is dry-run."""
    validate_manifest(manifest)
    backup_root = Path(backup_dir).expanduser() if backup_dir else Path.home() / ".local/state/lwa-mcp/agents-backups"
    changes = []
    for entry in manifest.get("projects", []):
        path = Path(entry["path"]).expanduser() / "AGENTS.md"
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        content = render_agents(existing, manifest["shared"], entry.get("delta", ""))
        change = SyncChange(path, content != existing, content)
        changes.append(change)
        if apply and change.changed:
            if path.exists():
                backup_root.mkdir(mode=0o700, parents=True, exist_ok=True)
                backup = backup_root / (path.as_posix().lstrip("/").replace("/", "__") + ".bak")
                shutil.copy2(path, backup)
            path.write_text(content, encoding="utf-8")
    return tuple(changes)
