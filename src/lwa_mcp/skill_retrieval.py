"""Small local semantic-ish index for skill descriptions.

The hashed vectors are deterministic and require no model or network access;
the index interface can later accept a higher-quality local embedding backend.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillMatch:
    name: str
    score: float


def _vector(text: str, dimensions: int = 128) -> list[float]:
    values = [0.0] * dimensions
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
        index = int.from_bytes(digest, "big") % dimensions
        values[index] += 1.0
    magnitude = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / magnitude for value in values]


def _tokens(text: str) -> set[str]:
    """Return normalized tokens for a deterministic lexical relevance signal."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class SkillIndex:
    """Versioned in-memory skill index with optional JSON persistence."""

    VERSION = 1

    def __init__(self, skills: dict[str, str]):
        if not skills:
            raise ValueError("skills must not be empty")
        self._skills = dict(skills)
        self._vectors = {name: _vector(description) for name, description in self._skills.items()}
        material = json.dumps(self._skills, sort_keys=True, separators=(",", ":"))
        self.fingerprint = hashlib.sha256(material.encode()).hexdigest()

    def search(self, query: str, *, limit: int = 4, threshold: float = 0.15) -> tuple[SkillMatch, ...]:
        """Return top matches above a score threshold, highest first."""
        if not query.strip():
            raise ValueError("query must be non-empty")
        if not 1 <= limit <= 20 or not 0 <= threshold <= 1:
            raise ValueError("limit or threshold is outside its allowed range")
        query_vector = _vector(query)
        query_tokens = _tokens(query)
        ranked = []
        for name, vector in self._vectors.items():
            cosine = sum(left * right for left, right in zip(query_vector, vector))
            lexical = len(query_tokens & _tokens(self._skills[name])) / max(len(query_tokens), 1)
            # Hash collisions help recall but can mis-rank short queries; shared
            # lexical terms provide a small, explainable tie-breaker.
            score = 0.7 * cosine + 0.3 * lexical
            if score >= threshold:
                ranked.append(SkillMatch(name, round(score, 6)))
        return tuple(sorted(ranked, key=lambda match: (-match.score, match.name))[:limit])

    def save(self, path: str | Path) -> None:
        """Persist the descriptions and index metadata without external data."""
        Path(path).write_text(json.dumps({"version": self.VERSION, "skills": self._skills}, indent=2), encoding="utf-8")

    @property
    def metadata(self) -> dict[str, object]:
        """Return stable index identity for telemetry and cache diagnostics."""
        return {"version": self.VERSION, "fingerprint": self.fingerprint, "skills": len(self._skills)}

    @classmethod
    def load(cls, path: str | Path, *, max_age_seconds: float | None = None) -> SkillIndex:
        """Load a version-compatible local index, optionally rejecting stale data."""
        cache_path = Path(path)
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"unable to read skill index: {path}") from exc
        if payload.get("version") != cls.VERSION or not isinstance(payload.get("skills"), dict):
            raise ValueError("unsupported or invalid skill index")
        if max_age_seconds is not None:
            if max_age_seconds < 0:
                raise ValueError("max_age_seconds must not be negative")
            age = max(0.0, time.time() - cache_path.stat().st_mtime)
            if age > max_age_seconds:
                raise ValueError(f"skill index is stale: age={age:.1f}s limit={max_age_seconds:.1f}s")
        return cls(payload["skills"])
