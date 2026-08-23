from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from typing import Any

from ..models import CompletionResult, ModelCandidate, ProviderConfig, RouteRequest


class ProviderError(RuntimeError):
    pass


_BEARER_RE = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+")
_SECRET_PARAM_RE = re.compile(
    r"(?i)([?&\s](?:api[_-]?key|token|secret|cookie|authorization)[=:\s]+)"
    r"([^\s&;,]+)"
)


def redact_error(message: str) -> str:
    """Remove credential material before provider errors reach logs or APIs."""
    redacted = _BEARER_RE.sub(r"\1[REDACTED]", str(message))
    redacted = _SECRET_PARAM_RE.sub(r"\1[REDACTED]", redacted)
    secret_names = (
        name
        for name in os.environ
        if any(fragment in name.upper() for fragment in ("KEY", "TOKEN", "SECRET", "COOKIE"))
    )
    for name in secret_names:
        value = os.getenv(name, "")
        if value and len(value) >= 4:
            redacted = redacted.replace(value, "[REDACTED]")
    return redacted[:2000]


class ProviderAdapter(ABC):
    def __init__(self, config: ProviderConfig):
        self.config = config

    def credential_envs(self, *, billing: bool = False) -> list[str]:
        """Return configured environment-variable names without exposing values."""
        if billing:
            names = [
                name
                for name in (self.config.billing_api_key_env, self.config.quota_key_env)
                if name
            ]
            if names:
                return list(dict.fromkeys(names))
        names = list(self.config.api_key_envs)
        if self.config.api_key_env:
            names.insert(0, self.config.api_key_env)
        return list(dict.fromkeys(names))

    def credential(self, *, billing: bool = False) -> tuple[str | None, str]:
        """Select the first configured credential in a named pool."""
        for env_name in self.credential_envs(billing=billing):
            if value := os.getenv(env_name, ""):
                return env_name, value
        return None, ""

    @abstractmethod
    async def complete(self, candidate: ModelCandidate, request: RouteRequest) -> CompletionResult:
        raise NotImplementedError

    async def list_models(self) -> list[ModelCandidate]:
        return []

    async def stream(self, candidate: ModelCandidate, request: RouteRequest):
        """Explicitly reject streaming until an adapter implements it safely."""
        raise ProviderError(f"{self.config.name}: streaming is not supported by this adapter")

    async def fetch_quota(self) -> dict[str, Any] | None:
        return None

    async def fetch_balance(self) -> dict[str, Any] | None:
        """Adapters may expose balances through the same official probe as quota."""
        return await self.fetch_quota()

    async def health(self) -> tuple[bool, str]:
        return True, "not probed"

    @staticmethod
    def decode_json(response: Any, context: str) -> dict[str, Any]:
        """Normalize malformed or non-object provider payloads to ProviderError."""
        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise ProviderError(f"{context}: malformed JSON response") from exc
        if not isinstance(payload, dict):
            raise ProviderError(f"{context}: response must be a JSON object")
        return payload

    @staticmethod
    def extract_rate_limits(headers: Any) -> dict[str, str]:
        result: dict[str, str] = {}
        for key, value in headers.items():
            low = key.lower()
            if any(fragment in low for fragment in ("rate", "limit", "remaining", "reset", "quota")):
                result[key] = str(value)
        return result
