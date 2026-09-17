"""Bounded, recoverable compression for noisy local tool output."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[^\s,]+"),
    re.compile(r"(?i)(token\s*[=:]\s*)[^\s,]+"),
)
_FAILURE_PATTERN = re.compile(r"(?i)(error|fail(?:ed|ure)?|panic|fatal|assert|traceback)")


@dataclass(frozen=True)
class CompressedOutput:
    text: str
    artifact: Path | None
    line_count: int
    failure_count: int


def redact_output(text: str) -> str:
    """Redact common credential forms before display or scratch persistence."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(r"\1[REDACTED]", text)
    return text


def compress_output(
    output: str,
    *,
    command: str = "tool",
    max_lines: int = 40,
    scratch_dir: str | os.PathLike[str] | None = None,
    persist: bool = True,
) -> CompressedOutput:
    """Return actionable lines and optionally persist the complete redacted output."""
    if not isinstance(output, str):
        raise TypeError("output must be a string")
    if not 1 <= max_lines <= 500:
        raise ValueError("max_lines must be between 1 and 500")

    safe_output = redact_output(output)
    lines = safe_output.splitlines()
    failures = [line for line in lines if _FAILURE_PATTERN.search(line)]
    if len(lines) <= max_lines:
        shown = lines
    else:
        failure_indexes = [index for index, line in enumerate(lines) if _FAILURE_PATTERN.search(line)]
        selected = set(range(min(max_lines // 2, len(lines))))
        selected.update(range(max(0, len(lines) - max_lines // 2), len(lines)))
        selected.update(failure_indexes)
        ordered = sorted(selected)
        shown = [lines[index] for index in ordered[:max_lines]]
    artifact = None
    if persist:
        directory = Path(scratch_dir) if scratch_dir else Path(tempfile.gettempdir()) / "lwa-mcp-output"
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=directory, prefix="output-", suffix=".log", delete=False
        ) as handle:
            artifact = Path(handle.name)
            handle.write(safe_output)
        artifact.chmod(0o600)
    omitted = max(0, len(lines) - len(shown))
    summary = [f"{command}: {len(lines)} lines, {len(failures)} failures"]
    summary.extend(shown)
    if omitted:
        summary.append(f"… {omitted} lines omitted")
    if artifact:
        summary.append(f"full output at {artifact} ({len(lines)} lines, {len(failures)} failures)")
    return CompressedOutput("\n".join(summary), artifact, len(lines), len(failures))
