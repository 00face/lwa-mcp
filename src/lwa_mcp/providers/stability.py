from __future__ import annotations

import base64
import time

import httpx

from ..config import STATE_DIR
from ..models import CompletionResult, ModelCandidate, RouteRequest
from .base import ProviderAdapter, ProviderError, redact_error


class StabilityAdapter(ProviderAdapter):
    async def complete(self, candidate: ModelCandidate, request: RouteRequest) -> CompletionResult:
        _, key = self.credential()
        if not key:
            raise ProviderError("stability: missing API key")
        endpoint = candidate.metadata.get("endpoint", "/v2beta/stable-image/generate/core")
        url = (self.config.base_url or "https://api.stability.ai").rstrip("/") + endpoint
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
                files={"none": (None, "")},
                data={
                    "prompt": request.prompt,
                    "output_format": request.metadata.get("output_format", "png"),
                    "aspect_ratio": request.metadata.get("aspect_ratio", "1:1"),
                },
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            raise ProviderError(
                f"stability HTTP {response.status_code}: {redact_error(response.text[:1000])}"
            )
        data = response.json()
        image_b64 = data.get("image")
        if not image_b64:
            raise ProviderError("stability response did not contain image")
        out_dir = STATE_DIR / "generated"
        out_dir.mkdir(parents=True, exist_ok=True)
        ext = request.metadata.get("output_format", "png")
        out = out_dir / f"stability-{int(time.time())}.{ext}"
        out.write_bytes(base64.b64decode(image_b64))
        return CompletionResult(
            provider=candidate.provider,
            model=candidate.model,
            text=str(out),
            latency_ms=latency_ms,
            response_id=data.get("seed"),
            rate_limits=self.extract_rate_limits(response.headers),
        )
