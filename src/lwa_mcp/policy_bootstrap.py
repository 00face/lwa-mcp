"""Fail-closed construction of policy-bound rite dependencies."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .local_evidence import make_local_evidence_collector
from .sandbox_policy import SandboxPolicy
from .signer_policy import SignerPolicy
from .sandbox_executor import probe_sandbox


def build_evidence_collector(policy_path: str | Path, runtime_probe: Callable[[], dict[str, Any]] | None = None):
    """Load both policies and return the collector used by ``run_rite``."""
    sandbox = SandboxPolicy.from_file(policy_path)
    signer = SignerPolicy.from_environment()
    if runtime_probe is None:
        def runtime_probe_for(path: Path) -> dict[str, Any]:
            return probe_sandbox(path, image=sandbox.image, memory=sandbox.memory, timeout=sandbox.timeout)
        def collector(image: str, output_dir: Path) -> dict[str, Any]:
            return make_local_evidence_collector(sandbox, signer, lambda: runtime_probe_for(output_dir))(image, output_dir)
        return collector
    return make_local_evidence_collector(sandbox, signer, runtime_probe)
