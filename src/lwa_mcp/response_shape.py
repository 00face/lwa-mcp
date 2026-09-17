"""Local diagnostics for unnecessarily over-structured responses."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ShapeDiagnostic:
    flagged: bool
    reason: str
    heading_count: int
    bullet_count: int


@dataclass(frozen=True)
class ShapePolicy:
    """Cheap, local thresholds for the response-shape format pass."""

    max_short_words: int = 40
    min_headings: int = 2
    min_bullets: int = 2


def lint_response(response: str, policy: ShapePolicy | None = None) -> ShapeDiagnostic:
    """Flag needless headings/bullets in short responses; never rewrite text."""
    if not isinstance(response, str) or not response.strip():
        raise ValueError("response must be non-empty text")
    lines = response.splitlines()
    headings = sum(1 for line in lines if re.match(r"^\s{0,3}#{1,6}\s+", line))
    bullets = sum(1 for line in lines if re.match(r"^\s*(?:[-*+] |\d+[.)] )", line))
    words = len(re.findall(r"\b\w+\b", response))
    selected = policy or ShapePolicy()
    flagged = (
        words <= selected.max_short_words
        and headings >= selected.min_headings
        and bullets >= selected.min_bullets
    )
    reason = "short response has multiple headings and bullet groups" if flagged else "structure is proportionate"
    return ShapeDiagnostic(flagged, reason, headings, bullets)
