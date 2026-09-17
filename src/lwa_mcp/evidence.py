"""Bounded, digest-linked evidence records for Agent Rites."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any

def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def evidence_record(image: str, *, attestation: str | Path, sbom: str | Path, vulnerabilities: str | Path, runtime: str | Path) -> dict[str, Any]:
    """Create a minimal record binding four on-disk artifacts to one image digest."""
    return {
        "schema": "lwa-evidence/v1",
        "image": image,
        "attestation": {"sha256": sha256_file(attestation)},
        "sbom": {"sha256": sha256_file(sbom)},
        "vulnerabilities": {"sha256": sha256_file(vulnerabilities)},
        "runtime": {"sha256": sha256_file(runtime)},
    }

def validate_evidence(record: dict[str, Any], image: str, *, required: tuple[str, ...] = ("attestation", "sbom", "vulnerabilities", "runtime")) -> dict[str, Any]:
    blockers = []
    if record.get("image") != image:
        blockers.append("evidence_digest_mismatch")
    for name in required:
        item = record.get(name)
        if not isinstance(item, dict) or not item.get("sha256"):
            blockers.append(f"evidence_missing:{name}")
    return {"schema": "lwa-evidence/v1", "image": image, "valid": not blockers, "blockers": blockers}

def write_evidence(path: str | Path, record: dict[str, Any]) -> None:
    payload = json.dumps(record, sort_keys=True, indent=2) + "\n"
    if len(payload.encode()) > 256 * 1024:
        raise ValueError("evidence record exceeds 256 KiB")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(target)
