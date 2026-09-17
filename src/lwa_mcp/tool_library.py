from __future__ import annotations

import json
import os
import re
import stat
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .models import LibraryTool, LibraryToolKind, LibraryToolStatus, TaskKind
from .syntax import parse_task_kind, validate_public_prompt_template

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9._+-]{1,}", re.IGNORECASE)


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value[:64] or "library-tool"


def _tokens(value: str) -> set[str]:
    return {part.lower() for part in _TOKEN_RE.findall(value)}


class ToolLibrary:
    """Persistent, cross-project library of reusable Lwa MCP workflows.

    Prompt recipes are safe-by-default and execute through the normal model router.
    Script entries may be cataloged, but remain non-executable until explicitly
    approved and script execution is enabled in configuration.
    """

    def __init__(self, root: Path):
        self.root = root
        self.tools_dir = root / "tools"
        self.registry_path = root / "registry.json"
        self.catalog_path = root / "CATALOG.md"
        self.readme_path = root / "README.md"
        self._ensure_layout()

    def _ensure_layout(self) -> None:
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            self._write_registry([])
        if not self.readme_path.exists():
            self.readme_path.write_text(self._library_readme(), encoding="utf-8")
        self.rebuild_catalog()

    def _read_registry(self) -> list[LibraryTool]:
        try:
            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = []
        return [LibraryTool.model_validate(item) for item in payload]

    def _write_registry(self, tools: list[LibraryTool]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temp = self.registry_path.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps([item.model_dump(mode="json") for item in tools], indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temp, self.registry_path)

    def list(self, status: LibraryToolStatus | str | None = None) -> list[LibraryTool]:
        rows = self._read_registry()
        if status is None:
            return sorted(rows, key=lambda item: item.updated_at, reverse=True)
        parsed = status if isinstance(status, LibraryToolStatus) else LibraryToolStatus(status)
        return sorted(
            [item for item in rows if item.status == parsed],
            key=lambda item: item.updated_at,
            reverse=True,
        )

    def get(self, slug: str) -> LibraryTool:
        target = slugify(slug)
        for tool in self._read_registry():
            if tool.slug == target:
                return tool
        raise KeyError(f"Unknown library tool: {slug}")

    def search(
        self,
        query: str,
        *,
        task: TaskKind | str | None = None,
        limit: int = 10,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        query_tokens = _tokens(query)
        parsed_task = parse_task_kind(task) if task else None
        ranked: list[tuple[float, LibraryTool]] = []
        for tool in self._read_registry():
            if active_only and tool.status != LibraryToolStatus.ACTIVE:
                continue
            haystack = " ".join(
                [tool.name, tool.description, *tool.tags, *tool.triggers, tool.task.value]
            )
            tool_tokens = _tokens(haystack)
            overlap = len(query_tokens & tool_tokens)
            union = len(query_tokens | tool_tokens) or 1
            score = overlap / union
            if parsed_task and tool.task == parsed_task:
                score += 0.35
            if query.lower() in haystack.lower():
                score += 0.4
            score += min(tool.confidence, 1.0) * 0.15
            score += min(tool.evidence_count, 20) / 200
            if score > 0 or not query.strip():
                ranked.append((score, tool))
        ranked.sort(key=lambda item: (item[0], item[1].updated_at), reverse=True)
        return [
            {"relevance": round(score, 4), **tool.model_dump(mode="json")}
            for score, tool in ranked[: max(1, min(limit, 50))]
        ]

    def create_prompt_tool(
        self,
        *,
        name: str,
        description: str,
        task: TaskKind | str,
        prompt_template: str,
        tags: list[str] | None = None,
        triggers: list[str] | None = None,
        created_by: str = "operator",
        pattern_signature: str | None = None,
        evidence_count: int = 0,
        confidence: float = 0.0,
        activate: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> LibraryTool:
        parsed_task = parse_task_kind(task)
        prompt_template = validate_public_prompt_template(prompt_template)
        existing = None
        registry = self._read_registry()
        if pattern_signature:
            existing = next(
                (item for item in registry if item.pattern_signature == pattern_signature), None
            )
        slug = existing.slug if existing else self._unique_slug(slugify(name), registry)
        now = datetime.now(UTC)
        tool = LibraryTool(
            slug=slug,
            name=name.strip(),
            description=description.strip(),
            version=self._next_version(existing.version) if existing else "0.1.0",
            kind=LibraryToolKind.PROMPT_RECIPE,
            status=(LibraryToolStatus.ACTIVE if activate else LibraryToolStatus.DRAFT),
            task=parsed_task,
            prompt_template=prompt_template,
            entrypoint="run.py",
            tags=sorted(set(tags or [])),
            triggers=sorted(set(triggers or [])),
            origin="pattern_detector" if pattern_signature else "operator",
            review_state="approved" if activate else "draft",
            safety_state="safe",
            created_by=created_by,
            pattern_signature=pattern_signature,
            evidence_count=evidence_count,
            confidence=max(0.0, min(confidence, 1.0)),
            approved=True,
            created_at=existing.created_at if existing else now,
            updated_at=now,
            metadata=metadata or {},
        )
        registry = [item for item in registry if item.slug != slug]
        registry.append(tool)
        self._write_registry(registry)
        self._write_tool_files(tool)
        self.rebuild_catalog()
        return tool

    def register_script(
        self,
        *,
        name: str,
        description: str,
        task: TaskKind | str,
        source: str,
        filename: str = "tool.py",
        tags: list[str] | None = None,
        triggers: list[str] | None = None,
    ) -> LibraryTool:
        safe_filename = Path(filename).name
        if Path(safe_filename).suffix.lower() != ".py":
            raise ValueError("Baseline script tools must use a .py entrypoint.")
        if len(source.encode("utf-8")) > 250_000:
            raise ValueError("Script source exceeds the 250 KB baseline limit.")
        registry = self._read_registry()
        slug = self._unique_slug(slugify(name), registry)
        now = datetime.now(UTC)
        tool = LibraryTool(
            slug=slug,
            name=name,
            description=description,
            kind=LibraryToolKind.SCRIPT,
            status=LibraryToolStatus.DRAFT,
            task=parse_task_kind(task),
            prompt_template="{input}",
            entrypoint=safe_filename,
            tags=sorted(set(tags or [])),
            triggers=sorted(set(triggers or [])),
            origin="operator",
            review_state="draft",
            safety_state="review_required",
            created_by="operator",
            approved=False,
            created_at=now,
            updated_at=now,
            metadata={"review_required": True},
        )
        registry.append(tool)
        self._write_registry(registry)
        directory = self.tools_dir / slug
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / tool.entrypoint
        target.write_text(source, encoding="utf-8")
        target.chmod(target.stat().st_mode | stat.S_IXUSR)
        self._write_manifest(tool)
        self._write_tool_readme(tool)
        self.rebuild_catalog()
        return tool

    def update_evidence(
        self,
        slug: str,
        *,
        evidence_count: int,
        confidence: float,
        metadata: dict[str, Any] | None = None,
    ) -> LibraryTool:
        registry = self._read_registry()
        tool = self.get(slug)
        merged_metadata = {**tool.metadata, **(metadata or {})}
        tool = tool.model_copy(
            update={
                "evidence_count": evidence_count,
                "confidence": max(0.0, min(confidence, 1.0)),
                "updated_at": datetime.now(UTC),
                "metadata": merged_metadata,
            }
        )
        registry = [item for item in registry if item.slug != tool.slug] + [tool]
        self._write_registry(registry)
        self._write_manifest(tool)
        self._write_tool_readme(tool)
        self.rebuild_catalog()
        return tool

    def set_status(
        self,
        slug: str,
        status: LibraryToolStatus | str,
        *,
        approved: bool | None = None,
    ) -> LibraryTool:
        parsed = status if isinstance(status, LibraryToolStatus) else LibraryToolStatus(status)
        registry = self._read_registry()
        tool = self.get(slug)
        update: dict[str, Any] = {"status": parsed, "updated_at": datetime.now(UTC)}
        if approved is not None:
            update["approved"] = approved
            update["review_state"] = "approved" if approved else "draft"
            update["safety_state"] = "safe" if approved else "review_required"
        tool = tool.model_copy(update=update)
        registry = [item for item in registry if item.slug != tool.slug] + [tool]
        self._write_registry(registry)
        self._write_manifest(tool)
        self._write_tool_readme(tool)
        self.rebuild_catalog()
        return tool

    def read_bundle(self, slug: str) -> dict[str, Any]:
        tool = self.get(slug)
        directory = self.tools_dir / tool.slug
        return {
            "tool": tool.model_dump(mode="json"),
            "path": str(directory),
            "readme": (directory / "README.md").read_text(encoding="utf-8"),
            "manifest": yaml.safe_load((directory / "tool.yaml").read_text(encoding="utf-8")),
        }

    def rebuild_catalog(self) -> Path:
        tools = self._read_registry() if self.registry_path.exists() else []
        lines = [
            "# Lwa MCP Tool Library Catalog",
            "",
            "This file is generated from `registry.json`. Use `search_tool_library` or ",
            "`lwa-router library search` to find reusable workflows.",
            "",
            "| Tool | Status | Kind | Task | Evidence | Confidence | Description |",
            "|---|---|---|---|---:|---:|---|",
        ]
        for tool in sorted(tools, key=lambda item: (item.status.value, item.name.lower())):
            description = tool.description.replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| `{tool.slug}` | {tool.status.value} | {tool.kind.value} | "
                f"{tool.task.value} | {tool.evidence_count} | {tool.confidence:.2f} | {description} |"
            )
        if not tools:
            lines.append("| _No tools yet_ | — | — | — | 0 | 0.00 | Repeated workflows will appear here. |")
        self.catalog_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self.catalog_path

    def summary(self) -> dict[str, Any]:
        tools = self._read_registry()
        return {
            "root": str(self.root),
            "total": len(tools),
            "active": sum(item.status == LibraryToolStatus.ACTIVE for item in tools),
            "draft": sum(item.status == LibraryToolStatus.DRAFT for item in tools),
            "generated": sum(item.created_by == "pattern_detector" for item in tools),
            "catalog": str(self.catalog_path),
        }

    def _write_tool_files(self, tool: LibraryTool) -> None:
        directory = self.tools_dir / tool.slug
        directory.mkdir(parents=True, exist_ok=True)
        runner = directory / "run.py"
        runner.write_text(self._runner_source(tool.slug), encoding="utf-8")
        runner.chmod(runner.stat().st_mode | stat.S_IXUSR)
        self._write_manifest(tool)
        self._write_tool_readme(tool)

    def _write_manifest(self, tool: LibraryTool) -> None:
        directory = self.tools_dir / tool.slug
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "tool.yaml").write_text(
            yaml.safe_dump(tool.model_dump(mode="json"), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    def _write_tool_readme(self, tool: LibraryTool) -> None:
        directory = self.tools_dir / tool.slug
        directory.mkdir(parents=True, exist_ok=True)
        generated = (
            f"Automatically detected from pattern `{tool.pattern_signature}` with "
            f"{tool.evidence_count} observations."
            if tool.pattern_signature
            else "Registered explicitly by the operator."
        )
        text = f"""# {tool.name}

{tool.description}

## Library identity

- Slug: `{tool.slug}`
- Version: `{tool.version}`
- Status: `{tool.status.value}`
- Kind: `{tool.kind.value}`
- Routed task: `{tool.task.value}`
- Origin: `{tool.origin}`
- Review state: `{tool.review_state}`
- Safety state: `{tool.safety_state}`
- Confidence: `{tool.confidence:.2f}`
- Evidence count: `{tool.evidence_count}`
- Provenance: {generated}

## When to use it

{os.linesep.join(f'- {item}' for item in tool.triggers) if tool.triggers else '- Use when the task matches the description above.'}

## MCP access

1. Call `search_tool_library` or `suggest_library_tools`.
2. Inspect this tool with `read_library_tool("{tool.slug}")`.
3. Execute it with `run_library_tool("{tool.slug}", input_text)`.

## CLI access

```bash
lwa-router library run {tool.slug} --input "your input"
```

The generated convenience wrapper accepts arguments or standard input:

```bash
{directory / tool.entrypoint} "your input"
printf '%s' "your input" | {directory / tool.entrypoint}
```

## Prompt recipe

```text
{tool.prompt_template}
```

## Safety

Prompt recipes always pass through normal Lwa MCP routing, consent, quota, and logging controls. Script tools require explicit review and approval before execution.
"""
        (directory / "README.md").write_text(text, encoding="utf-8")

    @staticmethod
    def _runner_source(slug: str) -> str:
        return f'''#!/usr/bin/env python3
"""Convenience launcher generated by Lwa MCP's persistent tool library."""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    content = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else sys.stdin.read().strip()
    if not content:
        print("Input is required as arguments or standard input.", file=sys.stderr)
        return 2
    command = ["lwa-router", "library", "run", "{slug}", "--input", "-"]
    return subprocess.run(command, input=content, text=True, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
'''

    @staticmethod
    def _next_version(version: str) -> str:
        try:
            major, minor, patch = (int(part) for part in version.split(".", 2))
            return f"{major}.{minor}.{patch + 1}"
        except (ValueError, TypeError):
            return "0.1.1"

    @staticmethod
    def _unique_slug(base: str, registry: list[LibraryTool]) -> str:
        occupied = {item.slug for item in registry}
        if base not in occupied:
            return base
        index = 2
        while f"{base}-{index}" in occupied:
            index += 1
        return f"{base}-{index}"

    @staticmethod
    def _library_readme() -> str:
        return """# Lwa MCP Persistent Tool Library

This directory is a user-level, cross-project library for reusable workflows detected or registered by Lwa MCP. It is intentionally stored under the XDG data directory rather than inside one project, allowing later MCP-enabled conversations and coding sessions to discover the same tools.

## Layout

- `registry.json` — machine-readable index.
- `CATALOG.md` — generated human-readable catalog.
- `tools/<slug>/tool.yaml` — versioned tool manifest.
- `tools/<slug>/README.md` — usage, origin, triggers, confidence, and safety notes.
- `tools/<slug>/run.py` — executable convenience wrapper.

## Conversation doctrine

When a task resembles prior work, call `suggest_library_tools` before recreating it. Use `run_library_tool` for a relevant active recipe. Record repeated successful workflows with `observe_workflow`; after the configured evidence threshold, Lwa MCP can create a reusable recipe and wrapper automatically.

Auto-generated prompt recipes are active by default only when configuration permits. Arbitrary script entries remain drafts until explicitly reviewed and approved.
"""
