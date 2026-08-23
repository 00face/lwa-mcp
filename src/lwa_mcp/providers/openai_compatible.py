from __future__ import annotations

import os
import time
from typing import Any

import httpx

from ..contracts import candidate_supported_parameters
from ..models import BillingClass, Capability, CompletionResult, ModelCandidate, RouteRequest
from ..syntax import api_reasoning_effort
from .base import ProviderAdapter, ProviderError, redact_error


def _first_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    if isinstance(value, list):
        values = [_first_number(v.get("value") if isinstance(v, dict) else v) for v in value]
        values = [v for v in values if v is not None]
        return min(values) if values else None
    return None


def _pricing_from_item(item: dict[str, Any]) -> tuple[float | None, float | None]:
    pricing = item.get("pricing") or item.get("pricings") or {}
    if not isinstance(pricing, dict):
        return None, None
    prompt = _first_number(pricing.get("prompt") or pricing.get("input"))
    completion = _first_number(pricing.get("completion") or pricing.get("output"))
    # OpenRouter values are dollars per token, while ZenMux values are per million.
    if prompt is not None and 0 < prompt < 0.01:
        prompt *= 1_000_000
    if completion is not None and 0 < completion < 0.01:
        completion *= 1_000_000
    return prompt, completion


class OpenAICompatibleAdapter(ProviderAdapter):
    def _key(self) -> str:
        _, value = self.credential()
        return value

    def _base(self) -> str:
        if not self.config.base_url:
            raise ProviderError(f"{self.config.name}: missing base_url")
        base = self.config.base_url.rstrip("/")
        if "{account_id}" in base:
            account = os.getenv(self.config.account_id_env or "", "")
            if not account:
                raise ProviderError(f"{self.config.name}: missing account id")
            base = base.replace("{account_id}", account)
        return base

    def _headers(self, key_env: str | None = None) -> dict[str, str]:
        headers = {"Content-Type": "application/json", **self.config.request_headers}
        key = os.getenv(key_env, "") if key_env else self._key()
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def _models_url(self) -> str:
        """Return the provider's configured OpenAI-compatible model URL."""
        return self._base() + self.config.models_path

    async def complete(self, candidate: ModelCandidate, request: RouteRequest) -> CompletionResult:
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        supported_parameters = candidate_supported_parameters(candidate)
        response_format = request.metadata.get("response_format")
        if response_format is not None and supported_parameters and "response_format" not in supported_parameters and "structured_outputs" not in supported_parameters:
            raise ProviderError(
                f"{self.config.name}: {candidate.model} does not advertise response_format support"
            )
        payload: dict[str, Any] = {
            "model": candidate.model,
            "messages": messages,
            "max_tokens": request.max_output_tokens,
            "temperature": 0.2 if request.task.value in {"verification", "document_editing", "sitrep"} else 0.45,
            "stream": False,
        }
        if request.reasoning_effort is not None:
            requested_effort = getattr(request.reasoning_effort, "value", str(request.reasoning_effort))
            if requested_effort not in candidate.reasoning_levels:
                advertised = ", ".join(candidate.reasoning_levels) or "none"
                raise ProviderError(
                    f"{self.config.name}: {candidate.model} does not advertise "
                    f"reasoning_effort={requested_effort!r} "
                    f"(advertised: {advertised})"
                )
            # This adapter currently targets /chat/completions, whose native
            # OpenAI-compatible field is reasoning_effort. The public Lwa
            # labels remain provider-neutral at the request boundary.
            payload["reasoning_effort"] = api_reasoning_effort(requested_effort)
        if response_format:
            payload["response_format"] = response_format
        payload.update(candidate.metadata.get("extra_body", {}))
        url = self._base() + self.config.chat_path
        credential_env, _credential_value = self.credential()
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(url, headers=self._headers(credential_env), json=payload)
        except httpx.TimeoutException as exc:
            raise ProviderError(f"{self.config.name}: request timed out") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            body = redact_error(response.text[:1000])
            raise ProviderError(f"{self.config.name} HTTP {response.status_code}: {body}")
        data = self.decode_json(response, f"{self.config.name} completion")
        choices = data.get("choices") or []
        if not choices:
            raise ProviderError(f"{self.config.name}: response had no choices")
        choice = choices[0]
        message = choice.get("message") or {}
        text = message.get("content")
        if isinstance(text, list):
            text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
        if text is None:
            text = data.get("output_text") or ""
        usage = data.get("usage") or {}
        usage_reported = any(
            key in usage
            for key in ("prompt_tokens", "input_tokens", "completion_tokens", "output_tokens")
        )
        prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        cost = usage.get("cost") or data.get("cost")
        if cost is None and candidate.input_cost_per_million is not None:
            cost = prompt_tokens * candidate.input_cost_per_million / 1_000_000
            if candidate.output_cost_per_million is not None:
                cost += completion_tokens * candidate.output_cost_per_million / 1_000_000
        return CompletionResult(
            provider=candidate.provider,
            model=str(data.get("model") or candidate.model),
            text=str(text),
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            cost_usd=float(cost) if cost is not None else None,
            latency_ms=latency_ms,
            finish_reason=choice.get("finish_reason"),
            response_id=data.get("id"),
            rate_limits=self.extract_rate_limits(response.headers),
            raw_usage=usage,
            usage_reported=usage_reported,
            credential_env=credential_env,
        )

    async def fetch_quota(self) -> dict[str, Any] | None:
        if not self.config.quota_path:
            return None
        url = self._base() + self.config.quota_path
        key_envs = self.credential_envs(billing=True) or self.credential_envs()
        key_env = next((name for name in key_envs if os.getenv(name, "")), None)
        if key_env is None and key_envs:
            raise ProviderError(f"{self.config.name}: missing configured billing API key")
        async with httpx.AsyncClient(timeout=min(self.config.timeout_seconds, 30.0)) as client:
            response = await client.get(url, headers=self._headers(key_env))
        if response.status_code >= 400:
            raise ProviderError(
                f"{self.config.name} quota HTTP {response.status_code}: "
                f"{redact_error(response.text[:500])}"
            )
        payload = response.json()
        return payload if isinstance(payload, dict) else {"value": payload}

    async def list_models(self) -> list[ModelCandidate]:
        if not self.config.supports_live_models:
            return []
        url = self._models_url()
        async with httpx.AsyncClient(timeout=min(self.config.timeout_seconds, 30.0)) as client:
            response = await client.get(url, headers=self._headers())
        if response.status_code >= 400:
            raise ProviderError(f"{self.config.name} model discovery HTTP {response.status_code}")
        payload = response.json()
        items = payload.get("data") or payload.get("models") or []
        found: list[ModelCandidate] = []
        for item in items[: self.config.catalog_model_limit]:
            if not isinstance(item, dict):
                continue
            model_id = item.get("id") or item.get("name")
            if not model_id:
                continue
            input_cost, output_cost = _pricing_from_item(item)
            billing = self.config.billing_class
            if (
                (input_cost in {0, None} and output_cost in {0, None})
                or str(model_id).endswith(":free")
            ):
                billing = BillingClass.FREE
            capabilities = {Capability.TEXT}
            caps = item.get("capabilities") or {}
            modalities = set(item.get("input_modalities") or item.get("inputModalities") or [])
            if isinstance(caps, dict) and caps.get("reasoning"):
                capabilities.add(Capability.REASONING)
            if "image" in modalities:
                capabilities.add(Capability.VISION)
            supported = set(item.get("supported_parameters") or [])
            reasoning_levels = item.get("reasoning_levels") or item.get("reasoningLevels") or []
            if not isinstance(reasoning_levels, list):
                reasoning_levels = []
            if "tools" in supported:
                capabilities.add(Capability.TOOLS)
            if "response_format" in supported or "structured_outputs" in supported:
                capabilities.add(Capability.STRUCTURED)
            context = item.get("context_length") or item.get("inputTokenLimit") or 8192
            found.append(
                ModelCandidate(
                    provider=self.config.name,
                    model=str(model_id),
                    display_name=item.get("display_name") or item.get("displayName") or item.get("name"),
                    billing_class=billing,
                    capabilities=capabilities,
                    service_tiers=sorted(str(value) for value in (item.get("service_tiers") or item.get("serviceTiers") or [])),
                    supported_parameters=supported,
                    reasoning_levels=[str(value) for value in reasoning_levels],
                    context_length=int(context or 8192),
                    input_cost_per_million=input_cost,
                    output_cost_per_million=output_cost,
                    source="live",
                    metadata={"raw": item},
                )
            )
        return found

    async def health(self) -> tuple[bool, str]:
        try:
            if self.config.supports_live_models:
                await self.list_models()
                return True, "model catalog reachable"
            return True, "configured; live model probe disabled"
        except Exception as exc:  # noqa: BLE001
            return False, redact_error(str(exc))
