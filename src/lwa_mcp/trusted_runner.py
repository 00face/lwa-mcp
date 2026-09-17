"""Allowlisted subprocess boundary for assurance tools."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

ALLOWED_TOOLS = frozenset({"cosign", "syft", "grype", "podman", "docker", "python"})

def trusted_run(command: Sequence[str], *, timeout: int, capture_output: bool = True) -> subprocess.CompletedProcess[str]:
    if not command or Path(command[0]).name not in ALLOWED_TOOLS:
        raise ValueError("command executable is not allowlisted")
    executable = Path(command[0])
    if not executable.is_absolute():
        resolved = shutil.which(command[0])
        if not resolved:
            raise FileNotFoundError(command[0])
        executable = Path(resolved).resolve()
    args = list(command[1:])
    name = executable.name
    if name == "cosign":
        argv = ["cosign", *args]
    elif name == "syft":
        argv = ["syft", *args]
    elif name == "grype":
        argv = ["grype", *args]
    elif name == "podman":
        argv = ["podman", *args]
    elif name == "docker":
        argv = ["docker", *args]
    else:
        argv = ["python", *args]
    return subprocess.run(argv, capture_output=capture_output, text=True, timeout=timeout, check=False, shell=False)
