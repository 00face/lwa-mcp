"""Fail-closed image signature and SBOM verification boundary."""
from __future__ import annotations
import shutil
import subprocess
import json
import re
from .trusted_runner import trusted_run
from typing import Any


def evaluate_grype_json(payload: str, *, max_critical: int = 0, max_high: int = 0, reject_eol: bool = True) -> dict[str, Any]:
    """Evaluate structured Grype output without trusting human-formatted text."""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return {"verified": False, "blockers": ["malformed_grype_output"]}
    matches = data.get("matches")
    if not isinstance(matches, list) or not all(isinstance(item, dict) for item in matches) or not isinstance(data.get("distro"), dict):
        return {"verified": False, "blockers": ["malformed_grype_output"]}
    counts = {severity: sum(1 for item in matches if item.get("vulnerability", {}).get("severity", "").lower() == severity) for severity in ("critical", "high", "medium", "low")}
    blockers = []
    distro = data["distro"]
    if reject_eol and distro.get("eol") is True:
        blockers.append("eol_distribution")
    if counts["critical"] > max_critical:
        blockers.append("critical_threshold_exceeded")
    if counts["high"] > max_high:
        blockers.append("high_threshold_exceeded")
    return {"verified": not blockers, "blockers": blockers, "counts": counts, "distro": distro.get("name")}

def verify_image_attestation(image: str, *, cosign_path: str | None = None, sbom_path: str | None = None, grype_path: str | None = None, expected_identity: str | None = None, oidc_issuer: str | None = None) -> dict[str, Any]:
    """Verify a digest-pinned image with Cosign and inspect an SBOM when tools exist."""
    blockers: list[str] = []
    if not re.fullmatch(r"[^\s@]+(?:/[^\s@]+)*@sha256:[0-9a-f]{64}", image):
        blockers.append("image_not_digest_pinned")
    cosign = cosign_path or shutil.which("cosign")
    sbom = sbom_path or shutil.which("syft")
    grype = grype_path or shutil.which("grype")
    if not cosign:
        blockers.append("cosign_unavailable")
    if not sbom:
        blockers.append("sbom_tool_unavailable")
    if not grype:
        blockers.append("vulnerability_scanner_unavailable")
    if blockers:
        return {"schema": "lwa-image-attestation/v1", "image": image, "verified": False, "blockers": blockers}
    verify_args = [cosign, "verify"]
    if expected_identity:
        verify_args += ["--certificate-identity", expected_identity]
    if oidc_issuer:
        verify_args += ["--certificate-oidc-issuer", oidc_issuer]
    signature = trusted_run([*verify_args, image], timeout=60)
    inventory = trusted_run([sbom, image, "-o", "json"], timeout=120)
    vulnerabilities = trusted_run([grype, image, "-o", "json", "--fail-on", "critical"], timeout=120)
    if signature.returncode:
        blockers.append("signature_verification_failed")
    if inventory.returncode:
        blockers.append("sbom_generation_failed")
    if vulnerabilities.returncode:
        blockers.append("critical_vulnerabilities_or_scan_failed")
    grype_result = evaluate_grype_json(getattr(vulnerabilities, "stdout", ""))
    if not grype_result["verified"]:
        blockers.extend(grype_result["blockers"])
    return {"schema": "lwa-image-attestation/v1", "image": image, "verified": not blockers,
            "signature_checked": True, "sbom_checked": True, "vulnerabilities_checked": True,
            "vulnerability_counts": grype_result.get("counts", {}), "blockers": sorted(set(blockers))}
