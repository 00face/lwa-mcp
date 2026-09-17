"""Explicit prompt-finalization boundary for LWA surfaces."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FinalizedPrompt:
    text: str
    mode: str
    status: str
    input_chars: int
    output_chars: int
    prompt_hash: str

    def public_json(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "status": self.status,
            "input_chars": self.input_chars,
            "output_chars": self.output_chars,
            "prompt_hash": self.prompt_hash,
        }


def finalize_prompt(prompt: str, *, mode: str = "semantic") -> FinalizedPrompt:
    """Finalize without claiming semantic compression when no model is configured.

    ``semantic`` is intentionally an explicit bypass until a governed LWA
    provider route is supplied. ``compact`` performs only deterministic,
    semantics-preserving whitespace cleanup.
    """
    normalized = prompt.replace("\r\n", "\n").replace("\r", "\n")
    if mode == "raw":
        text, status = normalized, "raw_bypass"
    elif mode == "compact":
        text = re.sub(r"[ \t]+$", "", normalized, flags=re.MULTILINE)
        text = re.sub(r"\n{3,}", "\n\n", text)
        status = "deterministic_compact"
    elif mode == "semantic":
        text, status = normalized, "semantic_unavailable_bypass"
    else:
        raise ValueError("prompt mode must be semantic, compact, or raw")
    return FinalizedPrompt(
        text=text,
        mode=mode,
        status=status,
        input_chars=len(prompt),
        output_chars=len(text),
        prompt_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )
