"""Protected, non-persisting Cosign signer policy."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any

class SignerPolicyError(ValueError):
    pass

@dataclass(frozen=True)
class SignerPolicy:
    identity: str
    issuer: str

    @classmethod
    def from_environment(cls, environ: dict[str, str] | None = None) -> "SignerPolicy":
        values = environ or __import__("os").environ
        identity, issuer = values.get("LWA_COSIGN_IDENTITY", ""), values.get("LWA_COSIGN_ISSUER", "")
        if not identity or not issuer or "*" in identity or "*" in issuer:
            raise SignerPolicyError("explicit signer identity and issuer are required")
        if not re.fullmatch(r"https://[^\s/]+(?:/[^\s]*)?", issuer):
            raise SignerPolicyError("issuer must be an HTTPS URL")
        return cls(identity, issuer)

    def cosign_args(self) -> list[str]:
        return ["--certificate-identity", self.identity, "--certificate-oidc-issuer", self.issuer]

    def redacted_status(self) -> dict[str, Any]:
        return {"configured": True, "identity_configured": bool(self.identity), "issuer_configured": bool(self.issuer)}
