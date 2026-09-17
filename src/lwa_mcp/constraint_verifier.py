"""Post-generation feasibility checks for HardGate candidates."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .constraints import ConstraintKernel

_SECRET = re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*[=:]\s*([^\s]+)")


def verify_candidate(root: str | Path, kernel: ConstraintKernel, *, changed_paths: list[str], files: dict[str, str], terminal: dict[str, bool]) -> dict[str, Any]:
    """Return a fail-closed promotion decision without changing ``root``."""
    failures: list[str] = []
    for path in changed_paths:
        if not kernel.check_path(path).allowed:
            failures.append(f"path:{path}")
        for match in _SECRET.finditer(files.get(path, "")):
            failures.append(f"secret:{match.group(1).upper()}")
    for check in ("tests", "lint"):
        if terminal.get(check) is not True:
            failures.append(f"terminal:{check}")
    return {"schema": "lwa-verification/v1", "promote": not failures, "failures": failures,
            "root": str(Path(root).resolve()), "changed_files": len(changed_paths)}
