"""Explicit disposable Git worktree boundary for agent candidates."""

from __future__ import annotations

import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class WorktreeError(RuntimeError):
    """Raised when an isolated candidate worktree cannot be established."""


@contextmanager
def disposable_worktree(repository: str | Path, destination: str | Path) -> Iterator[Path]:
    """Create and remove a detached candidate worktree around one operation."""
    repo = Path(repository).expanduser().resolve()
    target = Path(destination).expanduser().resolve()
    if not (repo / ".git").exists() or target.exists():
        raise WorktreeError("repository must contain .git and destination must not exist")
    try:
        result = subprocess.run(["git", "worktree", "add", "--detach", str(target), "HEAD"], cwd=repo, capture_output=True, text=True, check=False)
        if result.returncode:
            raise WorktreeError(result.stderr.strip() or "git worktree add failed")
        yield target
    finally:
        if target.exists():
            result = subprocess.run(["git", "worktree", "remove", "--force", str(target)], cwd=repo, capture_output=True, text=True, check=False)
            if result.returncode:
                raise WorktreeError(result.stderr.strip() or "git worktree removal failed")
