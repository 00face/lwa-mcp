"""Composition gate binding image attestation to runtime evidence."""
from __future__ import annotations
from typing import Any
from .evidence import validate_evidence

def evaluate_image_gate(*, image: str, attestation: dict[str, Any], runtime: dict[str, Any], evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    if "@sha256:" not in image:
        blockers.append("image_not_digest_pinned")
    if attestation.get("verified") is not True:
        blockers.extend(attestation.get("blockers", ["image_attestation_failed"]))
    if attestation.get("image") not in (None, image):
        blockers.append("attestation_digest_mismatch")
    if runtime.get("image") not in (None, image):
        blockers.append("runtime_digest_mismatch")
    required = {"rootless": True, "network_disabled": True, "read_only": True, "no_new_privs": True}
    for key, expected in required.items():
        if runtime.get(key) is not expected:
            blockers.append(f"runtime_{key}_required")
    if evidence is not None:
        evidence_result = validate_evidence(evidence, image)
        if not evidence_result["valid"]:
            blockers.extend(evidence_result["blockers"])
    return {"schema": "lwa-image-gate/v1", "image": image, "passed": not blockers, "blockers": blockers}
