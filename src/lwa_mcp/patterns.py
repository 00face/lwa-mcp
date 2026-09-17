from __future__ import annotations

import hashlib
import re
from typing import Any

from .config import LoadedConfig
from .db import UsageDB
from .models import RouteRequest, TaskKind
from .syntax import parse_task_kind
from .tool_library import ToolLibrary, slugify

_WORD_RE = re.compile(r"[a-z][a-z0-9_-]{2,}", re.IGNORECASE)
_STOPWORDS = {
    "about", "after", "again", "also", "and", "are", "been", "before", "being",
    "can", "could", "create", "does", "each", "from", "have", "into", "just",
    "make", "need", "only", "other", "please", "should", "that", "the", "their",
    "then", "there", "these", "they", "this", "through", "using", "want", "what",
    "when", "where", "which", "with", "would", "your",
}


class PatternDetector:
    def __init__(self, config: LoadedConfig, db: UsageDB, library: ToolLibrary):
        self.config = config
        self.db = db
        self.library = library

    def observe_request(self, request: RouteRequest, success: bool = True) -> dict[str, Any] | None:
        if not self.config.settings.auto_detect_patterns:
            return None
        if request.metadata.get("skip_pattern_detection") or request.metadata.get("library_tool_slug"):
            return None
        return self.observe(
            task=request.task,
            sample=request.prompt,
            workflow_name=request.metadata.get("workflow_name"),
            description=request.metadata.get("workflow_description"),
            project=request.metadata.get("project"),
            success=success,
            tags=request.metadata.get("workflow_tags") or [],
        )

    def observe(
        self,
        *,
        task: TaskKind | str,
        sample: str,
        workflow_name: str | None = None,
        description: str | None = None,
        project: str | None = None,
        success: bool = True,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        parsed_task = parse_task_kind(task)
        keywords = self._keywords(" ".join(filter(None, [workflow_name, description, sample])))
        signature = self._select_signature(parsed_task, workflow_name, keywords)
        existing = self.db.get_workflow_pattern(signature)
        occurrences = (existing["occurrences"] if existing else 0) + 1
        successes = (existing["successes"] if existing else 0) + int(success)
        confidence = self._confidence(occurrences, successes, bool(workflow_name))
        label = workflow_name or self._label(parsed_task, keywords)
        summary = description or self._description(parsed_task, keywords)
        prompt_hash = hashlib.sha256(sample.encode("utf-8")).hexdigest()
        pattern = self.db.upsert_workflow_pattern(
            signature=signature,
            task=parsed_task.value,
            label=label,
            description=summary,
            keywords=keywords,
            success=success,
            confidence=confidence,
            project=project,
            prompt_hash=prompt_hash,
        )
        created_tool = None
        if pattern.get("tool_slug"):
            self.library.update_evidence(
                pattern["tool_slug"],
                evidence_count=pattern["occurrences"],
                confidence=pattern["confidence"],
                metadata={"successes": pattern["successes"], "project": pattern.get("project")},
            )
        elif (
            self.config.settings.auto_create_library_tools
            and pattern["occurrences"] >= self.config.settings.pattern_min_occurrences
            and pattern["successes"] >= self.config.settings.pattern_min_occurrences
        ):
            created_tool = self._scaffold_tool(pattern, tags or [])
            self.db.bind_pattern_tool(signature, created_tool.slug)
            pattern["tool_slug"] = created_tool.slug
        return {
            "pattern": pattern,
            "created_tool": created_tool.model_dump(mode="json") if created_tool else None,
        }

    def analyze(self, limit: int = 100) -> dict[str, Any]:
        patterns = self.db.list_workflow_patterns(limit)
        created = []
        for pattern in patterns:
            if (
                self.config.settings.auto_create_library_tools
                and pattern["occurrences"] >= self.config.settings.pattern_min_occurrences
                and pattern["successes"] >= self.config.settings.pattern_min_occurrences
                and not pattern.get("tool_slug")
            ):
                tool = self._scaffold_tool(pattern, [])
                self.db.bind_pattern_tool(pattern["signature"], tool.slug)
                pattern["tool_slug"] = tool.slug
                created.append(tool.model_dump(mode="json"))
        return {"patterns": patterns, "created_tools": created}

    def _select_signature(
        self, task: TaskKind, workflow_name: str | None, keywords: list[str]
    ) -> str:
        if workflow_name:
            raw = f"{task.value}:named:{slugify(workflow_name)}"
            return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
        candidates = self.db.list_workflow_patterns(200)
        token_set = set(keywords)
        best_signature = None
        best_score = 0.0
        for item in candidates:
            if item["task"] != task.value:
                continue
            existing = set(item["keywords"])
            score = len(token_set & existing) / (len(token_set | existing) or 1)
            if score > best_score:
                best_score = score
                best_signature = item["signature"]
        if best_signature and best_score >= self.config.settings.pattern_similarity_threshold:
            return best_signature
        raw = f"{task.value}:{','.join(keywords[:8])}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]

    def _scaffold_tool(self, pattern: dict[str, Any], tags: list[str]):
        task = TaskKind(pattern["task"])
        name = pattern["label"].strip().title()
        prompt_template = (
            "Execute this established reusable workflow conservatively and completely.\n\n"
            f"Workflow: {pattern['description']}\n"
            "Preserve binding literals, file paths, version constraints, and operator decisions. "
            "Return a directly usable result and identify any validation that could not be performed.\n\n"
            "INPUT:\n{input}"
        )
        triggers = [
            f"A {task.value.replace('_', ' ')} request matching: {pattern['description']}",
            *[f"The request mentions {word}." for word in pattern["keywords"][:4]],
        ]
        return self.library.create_prompt_tool(
            name=name,
            description=pattern["description"],
            task=task,
            prompt_template=prompt_template,
            tags=sorted({task.value, *pattern["keywords"], *tags}),
            triggers=triggers,
            created_by="pattern_detector",
            pattern_signature=pattern["signature"],
            evidence_count=pattern["occurrences"],
            confidence=pattern["confidence"],
            activate=self.config.settings.auto_activate_prompt_tools,
            metadata={
                "project": pattern.get("project"),
                "successes": pattern["successes"],
                "autogenerated": True,
            },
        )

    @staticmethod
    def _keywords(text: str) -> list[str]:
        counts: dict[str, int] = {}
        for word in _WORD_RE.findall(text.lower()[:1600]):
            if word in _STOPWORDS or word.isdigit():
                continue
            counts[word] = counts.get(word, 0) + 1
        ranked = sorted(counts, key=lambda item: (-counts[item], item))
        return ranked[:10] or ["general", "workflow"]

    @staticmethod
    def _label(task: TaskKind, keywords: list[str]) -> str:
        detail = " ".join(keywords[:4])
        return f"{task.value.replace('_', ' ')} — {detail}"

    @staticmethod
    def _description(task: TaskKind, keywords: list[str]) -> str:
        return (
            f"Repeated {task.value.replace('_', ' ')} workflow involving "
            + ", ".join(keywords[:6])
            + "."
        )

    @staticmethod
    def _confidence(occurrences: int, successes: int, named: bool) -> float:
        success_rate = successes / max(occurrences, 1)
        score = 0.32 + min(occurrences, 8) * 0.07 + success_rate * 0.1 + (0.08 if named else 0)
        return round(min(score, 0.98), 4)
