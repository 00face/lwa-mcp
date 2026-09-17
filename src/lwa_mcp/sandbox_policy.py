"""Validated, reproducible policy for post-generation sandbox runs."""
from __future__ import annotations
import shutil
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml

class SandboxPolicyError(ValueError):
    pass

@dataclass(frozen=True)
class SandboxPolicy:
    runtime: str
    image: str
    memory: str = "512m"
    timeout: int = 600
    network: str = "none"

    @classmethod
    def from_file(cls, path: str | Path) -> "SandboxPolicy":
        try:
            data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise SandboxPolicyError(str(exc)) from exc
        if not isinstance(data, dict) or data.get("version") != 1:
            raise SandboxPolicyError("sandbox policy version 1 is required")
        runtime, image = data.get("runtime"), data.get("image")
        if runtime not in {"podman", "docker"} or not isinstance(image, str) or not image:
            raise SandboxPolicyError("runtime and image are required")
        if ":" not in image or not re.search(r"@sha256:[0-9a-f]{64}$", image):
            raise SandboxPolicyError("image must be pinned by sha256 digest")
        timeout = data.get("timeout", 600)
        if not isinstance(timeout, int) or not 1 <= timeout <= 3600:
            raise SandboxPolicyError("timeout must be between 1 and 3600 seconds")
        return cls(runtime, image, str(data.get("memory", "512m")), timeout, str(data.get("network", "none")))

    def probe(self) -> dict[str, Any]:
        available = shutil.which(self.runtime) is not None
        return {"schema": "lwa-sandbox-capability/v1", "runtime": self.runtime,
                "available": available, "image": self.image, "network": self.network,
                "timeout": self.timeout, "blockers": [] if available else [f"runtime_unavailable:{self.runtime}"]}
