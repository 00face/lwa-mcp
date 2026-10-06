from __future__ import annotations

import time
from typing import Any

import httpx

from ..models import Capability, CompletionResult, ModelCandidate, RouteRequest
from .base import ProviderAdapter, ProviderError, redact_error, security_denial


class AnthropicAdapter(ProviderAdapter):
    """Native Anthropic Messages API adapter."""

    def _key(self) -> str:
        _, value = self.credential()
        return value

    def _base(self) -> str:
        return (self.config.base_url or "https://api.anthropic.com").rstrip("/")

    def _headers(self) -> dict[str, str]:
        key = self._key()
        headers = {
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
            **self.config.request_headers,
        }
        if key:
            headers["x-api-key"] = key
        return headers

    async def complete(self, candidate: ModelCandidate, request: RouteRequest) -> CompletionResult:
        if not self._key():
            raise ProviderError("anthropic: missing API key", status_code=401)
        payload: dict[str, Any] = {
            "model": candidate.model,
            "max_tokens": request.max_output_tokens,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system_prompt:
            payload["system"] = request.system_prompt
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(self._base() + "/v1/messages", headers=self._headers(), json=payload)
        except httpx.TimeoutException as exc:
            raise ProviderError("anthropic: request timed out") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            body = redact_error(response.text[:1000])
            lower = body.lower()
            retry_after = None
            if response.status_code == 429:
                try:
                    retry_after = float(response.headers.get("retry-after", ""))
                except ValueError:
                    pass
            raise ProviderError(
                f"anthropic HTTP {response.status_code}: {body}",
                status_code=response.status_code,
                quota_exhausted=any(token in lower for token in ("quota", "credit", "monthly limit")),
                security_denied=security_denial(lower),
                retry_after_seconds=retry_after,
            )
        data = self.decode_json(response, "anthropic completion")
        content = data.get("content") or []
        text = "".join(item.get("text", "") for item in content if isinstance(item, dict))
        usage = data.get("usage") or {}
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        cost = None
        if candidate.input_cost_per_million is not None:
            cost = input_tokens * candidate.input_cost_per_million / 1_000_000
            cost += output_tokens * (candidate.output_cost_per_million or 0) / 1_000_000
        return CompletionResult(
            provider=candidate.provider,
            model=str(data.get("model") or candidate.model),
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            finish_reason=data.get("stop_reason"),
            response_id=data.get("id"),
            rate_limits=self.extract_rate_limits(response.headers),
            raw_usage=usage,
            usage_reported=bool(usage),
            credential_env=self.credential()[0],
        )

    async def list_models(self) -> list[ModelCandidate]:
        if not self.config.supports_live_models or not self._key():
            return []
        async with httpx.AsyncClient(timeout=min(self.config.timeout_seconds, 30.0)) as client:
            response = await client.get(self._base() + "/v1/models", headers=self._headers())
        if response.status_code >= 400:
            raise ProviderError(f"anthropic model discovery HTTP {response.status_code}", status_code=response.status_code)
        payload = self.decode_json(response, "anthropic model discovery")
        result = []
        for item in payload.get("data") or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            result.append(ModelCandidate(
                provider=self.config.name,
                model=str(item["id"]),
                display_name=item.get("display_name"),
                billing_class=self.config.billing_class,
                capabilities={Capability.TEXT, Capability.REASONING},
                context_length=200_000,
                source="live",
            ))
        return result[: self.config.catalog_model_limit]
