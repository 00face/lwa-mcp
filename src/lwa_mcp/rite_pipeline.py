"""Explicit, non-promoting recurrence pipeline composition."""

from __future__ import annotations

from pathlib import Path
import tempfile
import os
from typing import Any, Callable

from .rite_preflight import preflight
from .rite_state import RiteState
from .rites import RiteManifest
from .constraint_verifier import verify_candidate
from .constraints import ConstraintKernel
from .promotion import decide_promotion
from .worktree_transaction import disposable_worktree
from .image_gate import evaluate_image_gate


def run_rite(rite: RiteManifest, repository: str | Path, current_sha: str, state: RiteState, *, agent_runner: Callable[[Path, RiteManifest], dict[str, Any]] | None = None, promote: bool = False, kernel: ConstraintKernel | None = None, approved: bool = False, attestation: dict[str, Any] | None = None, image: str | None = None, runtime_evidence: dict[str, Any] | None = None, evidence: dict[str, Any] | None = None, evidence_collector: Callable[[str, Path], dict[str, Any]] | None = None, policy_path: str | Path | None = None, evidence_dir: str | Path | None = None) -> dict[str, Any]:
    decision = preflight(previous_sha=state.load().get("last_sha"), current_sha=current_sha, findings=[])
    if decision["decision"] == "skip":
        return {"status": "skipped", "blockers": [], "promoted": False}
    if agent_runner is None:
        return {"status": "blocked", "blockers": ["agent_runner_not_configured"], "promoted": False}
    if kernel is None:
        return {"status": "blocked", "blockers": ["constraint_kernel_not_configured"], "promoted": False, "decision": decision}
    if attestation is None or attestation.get("verified") is not True:
        blockers = (attestation or {}).get("blockers", ["image_attestation_required"])
        return {"status": "blocked", "blockers": list(blockers), "promoted": False, "decision": decision}
    if evidence_collector is None and policy_path is not None:
        from .policy_bootstrap import build_evidence_collector
        try:
            evidence_collector = build_evidence_collector(policy_path)
        except Exception as error:
            return {"status": "blocked", "blockers": ["policy_bootstrap_failed", type(error).__name__], "promoted": False, "decision": decision}
    if image is None or runtime_evidence is None or (evidence is None and evidence_collector is None):
        return {"status": "blocked", "blockers": ["image_gate_evidence_required"], "promoted": False, "decision": decision}
    if evidence is None and evidence_collector is not None:
        try:
            destination = Path(evidence_dir or os.environ.get("LWA_EVIDENCE_DIR", Path(repository) / ".lwa-evidence"))
            evidence = evidence_collector(image, destination)
        except Exception as error:
            return {"status": "blocked", "blockers": ["evidence_collection_failed", type(error).__name__], "promoted": False, "decision": decision}
    image_gate = evaluate_image_gate(image=image, attestation=attestation, runtime=runtime_evidence, evidence=evidence)
    if not image_gate["passed"]:
        return {"status": "blocked", "blockers": image_gate["blockers"], "promoted": False, "decision": decision, "image_gate": image_gate}
    repository = Path(repository).resolve()
    destination = Path(tempfile.mkdtemp(prefix=".lwa-rite-", dir=repository.parent))
    destination.rmdir()
    try:
        with disposable_worktree(repository, destination) as worktree:
            candidate = agent_runner(worktree, rite)
            verification = verify_candidate(worktree, kernel,
                changed_paths=list(candidate.get("changed_paths", [])),
                files=dict(candidate.get("files", {})),
                terminal=dict(candidate.get("terminal", {})))
            promotion = decide_promotion(verifier=verification,
                changed_files=verification["changed_files"], approved=approved,
                require_change=rite.require_change)
            if promote and promotion["status"] == "ready":
                return {"status": "blocked", "blockers": ["promotion_backend_not_configured"], "promoted": False, "verification": verification, "promotion": promotion}
            return {"status": promotion["status"], "blockers": promotion["blockers"], "promoted": False, "verification": verification, "promotion": promotion}
    finally:
        state.record(current_sha, success=False, metrics={}, findings=[])
