"""Local, explainable routing for a stable MCP proxy surface.

This module deliberately does not mutate ``tools/list``. MCP clients commonly
cache that response, so callers can use the result to select capabilities behind
a stable proxy or to decide which schemas to request from a separate host.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolProfile:
    name: str
    terms: frozenset[str]


DEFAULT_PROFILES = (
    ToolProfile("prepare_task", frozenset({"prepare", "preflight", "route", "model", "provider"})),
    ToolProfile("run_prepared_task", frozenset({"run", "execute", "approved", "plan", "provider"})),
    ToolProfile("verify_work", frozenset({"verify", "test", "tests", "testing", "check", "audit", "validate"})),
    ToolProfile("edit_document", frozenset({"edit", "rewrite", "document", "modify", "patch"})),
    ToolProfile("write_sitrep", frozenset({"sitrep", "status", "report", "evidence"})),
    ToolProfile("plan_work", frozenset({"plan", "roadmap", "work", "sequence", "task"})),
    ToolProfile("compress_conversation", frozenset({"compress", "conversation", "context", "summarize"})),
    ToolProfile("optimize_prompt", frozenset({"optimize", "prompt", "tokens", "shorten"})),
    ToolProfile("quick_response", frozenset({"quick", "short", "answer", "simple"})),
)


@dataclass(frozen=True)
class RoutingDecision:
    tools: tuple[str, ...]
    scores: tuple[tuple[str, int], ...]
    confidence: float
    fallback: bool


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def classify_intent(
    prompt: str,
    *,
    profiles: tuple[ToolProfile, ...] = DEFAULT_PROFILES,
    limit: int = 4,
    minimum_score: int = 1,
) -> RoutingDecision:
    """Return deterministic top tool candidates without a model call."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")
    if not 1 <= limit <= 8:
        raise ValueError("limit must be between 1 and 8")

    words = _tokens(prompt)
    ranked = sorted(
        ((profile.name, len(words & profile.terms)) for profile in profiles),
        key=lambda item: (-item[1], item[0]),
    )
    matches = tuple(item for item in ranked if item[1] >= minimum_score)[:limit]
    fallback = not matches
    selected = tuple(name for name, _ in matches)
    if fallback:
        selected = tuple(profile.name for profile in profiles[:limit])
    best = matches[0][1] if matches else 0
    second = matches[1][1] if len(matches) > 1 else 0
    confidence = 0.0 if fallback else min(1.0, (best + max(0, best - second)) / 4)
    return RoutingDecision(selected, matches, confidence, fallback)
