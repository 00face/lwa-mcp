from __future__ import annotations

from typing import Any

from ..codex_app_server import CodexAppServerClient, normalize_rate_limits
from ..models import CompletionResult, ModelCandidate, RouteRequest
from .base import ProviderAdapter


class CodexAppServerAdapter(ProviderAdapter):
    def _client(self) -> CodexAppServerClient:
        return CodexAppServerClient(timeout_seconds=self.config.timeout_seconds)

    async def fetch_quota(self) -> dict[str, Any] | None:
        result = await self._client().read_rate_limits()
        return normalize_rate_limits(result)

    async def fetch_usage(self) -> dict[str, Any]:
        return await self._client().read_usage()

    async def list_models(self) -> list[ModelCandidate]:
        return []

    async def complete(self, candidate: ModelCandidate, request: RouteRequest) -> CompletionResult:
        text, metadata = await self._client().complete(
            model=candidate.model,
            prompt=request.prompt,
            system_prompt=request.system_prompt,
        )
        return CompletionResult(
            provider=candidate.provider,
            model=candidate.model,
            text=text,
            response_id=metadata.get("id"),
            raw_usage=metadata.get("usage") or {},
            usage_reported=bool(metadata.get("usage")),
            credential_env="Codex app-server OAuth session",
        )
