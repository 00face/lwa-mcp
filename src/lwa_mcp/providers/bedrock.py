from __future__ import annotations

import asyncio
import time
from typing import Any

from ..models import Capability, CompletionResult, ModelCandidate, RouteRequest
from .base import ProviderAdapter, ProviderError, redact_error


class BedrockAdapter(ProviderAdapter):
    """AWS Bedrock Converse adapter using the ambient AWS credential chain."""

    def _client(self):
        try:
            import boto3
        except ImportError as exc:
            raise ProviderError("bedrock: install the bedrock optional dependency") from exc
        return boto3.client("bedrock-runtime", region_name=self.config.region)

    async def complete(self, candidate: ModelCandidate, request: RouteRequest) -> CompletionResult:
        def call() -> dict[str, Any]:
            messages = [{"role": "user", "content": [{"text": request.prompt}]}]
            kwargs: dict[str, Any] = {
                "modelId": candidate.model,
                "messages": messages,
                "inferenceConfig": {"maxTokens": request.max_output_tokens},
            }
            if request.system_prompt:
                kwargs["system"] = [{"text": request.system_prompt}]
            return self._client().converse(**kwargs)

        started = time.perf_counter()
        try:
            data = await asyncio.to_thread(call)
        except Exception as exc:
            detail = redact_error(str(exc))
            lower = detail.lower()
            throttled = any(marker in lower for marker in ("throttl", "too many requests", "rate exceeded"))
            quota = any(marker in lower for marker in ("quota", "servicequotaexceeded", "limit exceeded"))
            raise ProviderError(
                f"bedrock: {detail}",
                status_code=429 if throttled else None,
                quota_exhausted=quota and not throttled,
            ) from exc
        output = data.get("output") or {}
        message = output.get("message") or {}
        text = "".join(item.get("text", "") for item in message.get("content") or [] if isinstance(item, dict))
        usage = data.get("usage") or {}
        return CompletionResult(
            provider=candidate.provider,
            model=candidate.model,
            text=text,
            input_tokens=int(usage.get("inputTokens") or 0),
            output_tokens=int(usage.get("outputTokens") or 0),
            latency_ms=int((time.perf_counter() - started) * 1000),
            finish_reason=(data.get("stopReason")),
            raw_usage=usage,
            usage_reported=bool(usage),
            credential_env="AWS credential chain",
        )

    async def list_models(self) -> list[ModelCandidate]:
        def call():
            return self._client().list_foundation_models(byOutputModality="TEXT")

        try:
            payload = await asyncio.to_thread(call)
        except Exception as exc:
            raise ProviderError(f"bedrock model discovery: {redact_error(str(exc))}") from exc
        result = []
        for item in payload.get("modelSummaries") or []:
            model_id = item.get("modelId")
            if model_id:
                result.append(ModelCandidate(
                    provider=self.config.name,
                    model=model_id,
                    display_name=item.get("modelName"),
                    billing_class=self.config.billing_class,
                    capabilities={Capability.TEXT, Capability.REASONING},
                    context_length=200_000,
                    source="live",
                ))
        return result[: self.config.catalog_model_limit]
