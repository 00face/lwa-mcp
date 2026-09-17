"""Read-only Codex pet configuration and source-policy handshake."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CodexPetProbe:
    config_path: str
    config_present: bool
    native_opt_in: bool
    configured: bool
    source: str
    reason: str

    def public_json(self) -> dict[str, object]:
        return {
            "config_path": self.config_path,
            "config_present": self.config_present,
            "native_opt_in": self.native_opt_in,
            "configured": self.configured,
            "source": self.source,
            "reason": self.reason,
        }


def probe_codex_pet(*, config_path: Path | None = None, env: dict[str, str] | None = None) -> CodexPetProbe:
    """Inspect Codex pet policy without mutating configuration or assets."""
    values = env if env is not None else os.environ
    path = config_path or Path(values.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"
    present = path.is_file()
    text = path.read_text(encoding="utf-8", errors="replace") if present else ""
    opted_in = values.get("LWA_NATIVE_CODEX_PET", "off").lower() in {"1", "true", "yes", "on"}
    disabled = 'pet=""' in text or "pet = \"\"" in text
    configured = "pet" in text
    if opted_in and not disabled:
        source, reason = "codex-native", "explicit native pet opt-in"
    elif disabled:
        source, reason = "lwa-fallback", "Codex pet is explicitly suppressed"
    elif not present:
        source, reason = "lwa-fallback", "Codex config is unavailable"
    else:
        source, reason = "codex-native-candidate", "Codex config inspected; host graphics still require validation"
    return CodexPetProbe(str(path), present, opted_in, configured, source, reason)
