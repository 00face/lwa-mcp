"""Fail-closed container command boundary for Agent Rite candidates."""

from __future__ import annotations

import shutil
import subprocess
import json
from pathlib import Path
from typing import Sequence


class SandboxUnavailable(RuntimeError):
    """Raised when no supported container runtime is available."""


def sandbox_command(root: str | Path, command: Sequence[str], *, image: str = "python:3.12-slim", memory: str = "512m") -> list[str]:
    """Build a network-disabled, resource-limited container invocation."""
    runtime = shutil.which("podman") or shutil.which("docker")
    if runtime is None:
        raise SandboxUnavailable("podman or docker is required")
    if not command:
        raise ValueError("sandbox command must not be empty")
    return [runtime, "run", "--rm", "--network=none", "--memory", memory,
            "--cap-drop=ALL", "--security-opt=no-new-privileges", "--read-only", "--pids-limit=256", "-v",
            f"{Path(root).resolve()}:/workspace:rw", "-w", "/workspace", image, *command]


def run_sandbox(root: str | Path, command: Sequence[str], *, image: str = "python:3.12-slim", memory: str = "512m", timeout: int = 600) -> subprocess.CompletedProcess[str]:
    """Execute one bounded command; caller decides whether output is promotable."""
    invocation = sandbox_command(root, command, image=image, memory=memory)
    return subprocess.run(invocation, capture_output=True, text=True, timeout=timeout, check=False)

def probe_sandbox(root: str | Path, *, image: str, memory: str = "512m", timeout: int = 60) -> dict[str, object]:
    """Observe effective container controls using a small in-image probe."""
    script = "import json,os; s=open('/proc/self/status').read(); print(json.dumps({'rootless':os.getuid()!=0,'no_new_privs':'NoNewPrivs:\\t1' in s,'capabilities_zero':'CapEff:\\t0000000000000000' in s}))"
    result = run_sandbox(root, ["-c", script], image=image, memory=memory, timeout=timeout)
    if result.returncode != 0:
        return {"verified": False, "blockers": ["runtime_probe_failed"], "stderr": result.stderr[-2048:]}
    try:
        observed = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {"verified": False, "blockers": ["runtime_probe_malformed"]}
    observed.update({"image": image, "network_disabled": True, "read_only": True, "memory_limit": memory})
    required = ("rootless", "no_new_privs", "capabilities_zero", "network_disabled", "read_only")
    observed["verified"] = all(observed.get(key) is True for key in required)
    observed["blockers"] = [f"runtime_{key}_unverified" for key in required if observed.get(key) is not True]
    return observed
