"""Canonical validation for public Lwa task, quality, and prompt syntax."""

from __future__ import annotations

import re
from typing import Final

from .models import ReasoningEffort, TaskKind

QUALITY_VALUES: Final[tuple[str, ...]] = ("economy", "balanced", "high")
REASONING_EFFORT_VALUES: Final[tuple[str, ...]] = tuple(item.value for item in ReasoningEffort)
API_REASONING_EFFORT: Final[dict[str, str]] = {
    ReasoningEffort.INSTANT.value: "none",
    ReasoningEffort.MEDIUM.value: "medium",
    ReasoningEffort.HIGH.value: "high",
}
PUBLIC_TEMPLATE_VARIABLES: Final[frozenset[str]] = frozenset({"input"})
INTERNAL_TEMPLATE_VARIABLES: Final[frozenset[str]] = frozenset({"CONSENSUS_TRANSCRIPT"})
_VARIABLE_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def parse_task_kind(value: TaskKind | str) -> TaskKind:
    """Parse a canonical task value and report the complete accepted set."""
    if isinstance(value, TaskKind):
        return value
    try:
        return TaskKind(value)
    except (TypeError, ValueError) as exc:
        accepted = ", ".join(item.value for item in TaskKind)
        raise ValueError(f"Invalid task {value!r}; expected one of: {accepted}") from exc


def validate_quality(value: str) -> str:
    """Validate the public quality vocabulary before request construction."""
    if value not in QUALITY_VALUES:
        accepted = ", ".join(QUALITY_VALUES)
        raise ValueError(f"Invalid quality {value!r}; expected one of: {accepted}")
    return value


def validate_reasoning_effort(value: str | None) -> str | None:
    """Validate Lwa's explicit provider reasoning effort, if supplied."""
    if value is None:
        return None
    if value not in REASONING_EFFORT_VALUES:
        accepted = ", ".join(REASONING_EFFORT_VALUES)
        raise ValueError(f"Invalid reasoning_effort {value!r}; expected one of: {accepted}")
    return value


def api_reasoning_effort(value: str) -> str:
    """Map Lwa's public effort label to the OpenAI-compatible wire value."""
    try:
        return API_REASONING_EFFORT[value]
    except KeyError as exc:
        raise ValueError(f"Unsupported reasoning effort: {value}") from exc


def validate_public_prompt_template(template: str) -> str:
    """Require at least one public ``{input}`` variable and no other braces."""
    if not isinstance(template, str) or not template.strip():
        raise ValueError("Prompt template must be a non-empty string containing {input}.")
    if "{{CONSENSUS_TRANSCRIPT}}" in template:
        raise ValueError("{{CONSENSUS_TRANSCRIPT}} is reserved for internal consensus synthesis.")
    matches = list(_VARIABLE_RE.finditer(template))
    names = {match.group(1) for match in matches}
    unknown = names - PUBLIC_TEMPLATE_VARIABLES
    if unknown:
        raise ValueError(
            "Unsupported prompt template variable(s): "
            + ", ".join(sorted(unknown))
            + "; expected only {input}."
        )
    remainder = _VARIABLE_RE.sub("", template)
    if "{" in remainder or "}" in remainder:
        raise ValueError("Prompt template contains malformed braces; expected only {input}.")
    if "input" not in names:
        raise ValueError("Prompt template must contain the {input} variable.")
    return template.strip()


def syntax_contract() -> dict[str, object]:
    """Return the public contract for MCP/CLI/docs and diagnostics."""
    return {
        "tasks": [item.value for item in TaskKind],
        "qualities": list(QUALITY_VALUES),
        "reasoning_efforts": list(REASONING_EFFORT_VALUES),
        "reasoning_effort_mapping": dict(API_REASONING_EFFORT),
        "public_template_variables": sorted(PUBLIC_TEMPLATE_VARIABLES),
        "internal_template_variables": sorted(INTERNAL_TEMPLATE_VARIABLES),
    }
