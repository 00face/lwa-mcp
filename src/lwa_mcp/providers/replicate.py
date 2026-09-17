from __future__ import annotations

import time
from typing import Any

import httpx

from ..models import CompletionResult, ModelCandidate, RouteRequest
from .base import ProviderAdapter, ProviderError, redact_error


class ReplicateAdapter(ProviderAdapter):
    """Baseline adapter for a configured Replicate official/community model.

    Each seed model must define metadata.input_mapping. For text models the default
    payload is {"prompt": request.prompt}. Image output URLs are returned as JSON text.
    """

    async def complete(self, candidate: ModelCandidate, request: RouteRequest) -> CompletionResult:
        _, token = self.credential()
        if not token:
            raise ProviderError("replicate: missing API token")
        parts = candidate.model.split("/", 1)
        if len(parts) != 2:
            raise ProviderError("replicate model must be owner/name")
        url = f"https://api.replicate.com/v1/models/{parts[0]}/{parts[1]}/predictions"
        mapping: dict[str, Any] = candidate.metadata.get("input_mapping") or {"prompt": request.prompt}
        mapping = {k: (request.prompt if v == "$PROMPT" else v) for k, v in mapping.items()}
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Prefer": "wait=60",
                },
                json={"input": mapping},
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            raise ProviderError(
                f"replicate HTTP {response.status_code}: {redact_error(response.text[:1000])}"
            )
        data = response.json()
        output = data.get("output")
        if isinstance(output, list):
            text = "\n".join(str(item) for item in output)
        elif isinstance(output, dict):
            import json

            text = json.dumps(output, indent=2)
        else:
            text = str(output or "")
        metrics = data.get("metrics") or {}
        return CompletionResult(
            provider=candidate.provider,
            model=candidate.model,
            text=text,
            latency_ms=latency_ms,
            response_id=data.get("id"),
            rate_limits=self.extract_rate_limits(response.headers),
            raw_usage=metrics,
        )
