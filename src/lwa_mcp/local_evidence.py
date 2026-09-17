"""Collect reproducible, digest-bound local assurance artifacts."""
from __future__ import annotations

import subprocess
import json
from pathlib import Path
from typing import Any, Callable

from .evidence import evidence_record, write_evidence

def make_local_evidence_collector(sandbox_policy: Any, signer_policy: Any, runtime_probe: Callable[[], dict[str, Any]]) -> Callable[[str, Path], dict[str, Any]]:
    """Build a pipeline-compatible collector from validated deployment policies."""
    def collect(image: str, output_dir: Path) -> dict[str, Any]:
        if image != sandbox_policy.image:
            raise ValueError("image does not match sandbox policy")
        return collect_local_evidence(image, output_dir, cosign_args=["cosign", *signer_policy.cosign_args()], runtime_probe=runtime_probe)
    return collect


def collect_local_evidence(
    image: str,
    output_dir: str | Path,
    *,
    cosign_args: list[str],
    runtime_probe: Callable[[], dict[str, Any]],
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Run assurance tools, persist bounded artifacts, and return their manifest."""
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    attestation = target / "attestation.json"
    sbom = target / "sbom.json"
    vulnerabilities = target / "vulnerabilities.json"
    runtime = target / "runtime.json"
    commands = (
        ([*cosign_args, "verify", image], attestation),
        (["syft", image, "-o", "json"], sbom),
        (["grype", image, "-o", "json", "--fail-on", "critical"], vulnerabilities),
    )
    for command, destination in commands:
        result = runner(command, capture_output=True, text=True, timeout=180, check=False)
        destination.write_text(result.stdout or "", encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"assurance command failed: {command[0]}")
    runtime_result = runtime_probe()
    if runtime_result.get("verified") is not True:
        raise RuntimeError("runtime probe did not verify sandbox controls")
    runtime.write_text(json.dumps(runtime_result, sort_keys=True), encoding="utf-8")
    record = evidence_record(image, attestation=attestation, sbom=sbom, vulnerabilities=vulnerabilities, runtime=runtime)
    write_evidence(target / "evidence.json", record)
    return record
