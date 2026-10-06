"""Small, provider-free capability-cache helpers for Lwa handshakes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def base_identity(command: list[str], root: Path) -> dict[str, Any]:
    return {
        "root": str(root),
        "command": list(command),
        "config_fingerprint": hashlib.sha256(
            json.dumps({"root": str(root), "command": command}, sort_keys=True).encode()
        ).hexdigest(),
    }


def manifest_is_complete(manifest: Any) -> bool:
    if not isinstance(manifest, dict):
        return False
    required = ("protocol_version", "tools", "resources", "prompts")
    if not all(manifest.get(key) for key in required):
        return False
    return (
        all(isinstance(manifest[key], list) and manifest[key] for key in required[1:])
        and len(manifest["tools"]) >= 4
        and len(manifest["resources"]) >= 2
    )


def save_cache(path: Path, identity: dict[str, Any], manifest: dict[str, Any]) -> None:
    payload = {"identity": identity, "cache_key": hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest(), "manifest": manifest}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def load_cache(path: Path, identity: dict[str, Any]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if payload.get("identity") != identity or not manifest_is_complete(payload.get("manifest")):
        return None
    return payload
