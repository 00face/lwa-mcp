"""Resolve and lint the layered AGENTS instruction hierarchy."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentsResolution:
    paths: tuple[Path, ...]
    merged_text: str


def resolve_agents(cwd: str | Path, *, codex_home: str | Path | None = None) -> AgentsResolution:
    """Return existing instruction files from global scope to the requested cwd."""
    target = Path(cwd).expanduser().resolve()
    if not target.is_dir():
        raise ValueError(f"cwd is not a directory: {cwd}")
    home = Path(codex_home).expanduser().resolve() if codex_home else Path.home() / ".codex"
    repo = _repository_root(target)
    candidates = [home / "AGENTS.override.md", home / "AGENTS.md", repo / "AGENTS.md"]
    try:
        relative_parts = target.relative_to(repo).parts
    except ValueError:
        relative_parts = ()
    current = repo
    for part in relative_parts:
        current /= part
        candidates.extend((current / "AGENTS.md", current / "AGENTS.override.md"))
    paths = tuple(dict.fromkeys(path for path in candidates if path.is_file()))
    return AgentsResolution(paths, "\n\n".join(path.read_text(encoding="utf-8") for path in paths))


def _repository_root(path: Path) -> Path:
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return path


def upsert_section(path: str | Path, section_header: str, body: str) -> Path:
    """Idempotently replace or append a tagged markdown section."""
    if not section_header.strip() or not body.strip():
        raise ValueError("section_header and body must be non-empty")
    target = Path(path).expanduser()
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    marker = f"<!-- lwa-mcp:section={section_header.strip()} -->"
    block = f"{marker}\n## {section_header.strip()}\n{body.strip()}"
    pattern = re.compile(re.escape(marker) + r".*?(?=\n<!-- lwa-mcp:section=|\Z)", re.DOTALL)
    result = pattern.sub(block, existing, count=1) if marker in existing else existing.rstrip() + "\n\n" + block
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(result.rstrip() + "\n", encoding="utf-8")
    return target


def lint_agents(resolution: AgentsResolution, *, max_bytes: int = 32768) -> tuple[str, ...]:
    """Report size, duplicate, and basic contradictory instruction warnings."""
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    warnings = []
    for path in resolution.paths:
        size = path.stat().st_size
        if size >= int(max_bytes * 0.9):
            warnings.append(f"near byte cap: {path} ({size}/{max_bytes})")
    lowered = resolution.merged_text.lower()
    if "prefer shell" in lowered and "prefer mcp" in lowered:
        warnings.append("contradictory preference: shell and MCP")
    headings = re.findall(r"^##\s+(.+)$", resolution.merged_text, re.MULTILINE)
    warnings.extend(f"duplicate section: {heading}" for heading in sorted({heading.lower() for heading in headings if headings.count(heading) > 1}))
    return tuple(warnings)
