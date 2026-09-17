"""Stable workspace/project roots carried through Lwa-launched processes."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkspaceContext:
    workspace_root: str
    project_root: str

    @property
    def environment(self) -> dict[str, str]:
        return {"LWA_WORKSPACE_ROOT": self.workspace_root, "LWA_PROJECT_ROOT": self.project_root}


def resolve_context(start: str | Path | None = None) -> WorkspaceContext:
    workspace = Path(start or os.getcwd()).expanduser().resolve()
    if not workspace.is_dir():
        raise ValueError("workspace root is not a directory")
    project = workspace
    for candidate in (workspace, *workspace.parents):
        if (candidate / ".git").exists():
            project = candidate
            break
    return WorkspaceContext(str(workspace), str(project))


def child_environment(start: str | Path | None = None) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(resolve_context(start).environment)
    return environment
