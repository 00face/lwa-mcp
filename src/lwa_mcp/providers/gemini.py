from __future__ import annotations

import time
from typing import Any

import httpx

from ..models import Capability, CompletionResult, ModelCandidate, RouteRequest
from .base import ProviderAdapter, ProviderError, redact_error


class GeminiAdapter(ProviderAdapter):
    """Native Google Gemini GenerateContent REST adapter."""

    def _key(self) -> str:
        _, value = self.credential()
        return value

    def _base(self) -> str:
        if not self.config.base_url:
            raise ProviderError(f"{self.config.name}: missing base_url")
        return self.config.base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", **self.config.request_headers}
        key = self._key()
        if key:
            headers["x-goog-api-key"] = key
        return headers

    @staticmethod
    def _model_name(model: str) -> str:
        return model.removeprefix("models/")

    async def complete(self, candidate: ModelCandidate, request: RouteRequest) -> CompletionResult:
        if request.metadata.get("response_format") is not None:
            supported_parameters = set(candidate.supported_parameters)
            if candidate.metadata.get("raw") and isinstance(candidate.metadata["raw"], dict):
                raw = candidate.metadata["raw"]
                for key in ("supported_parameters", "supportedParameters"):
                    value = raw.get(key)
                    if isinstance(value, (list, tuple, set)):
                        supported_parameters.update(str(item) for item in value)
            if supported_parameters and "response_format" not in supported_parameters:
                raise ProviderError(
                    f"{self.config.name}: {candidate.model} does not advertise response_format support"
                )
        contents = [{"role": "user", "parts": [{"text": request.prompt}]}]
        payload: dict[str, Any] = {"contents": contents}
        if request.system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": request.system_prompt}]}
        generation_config: dict[str, Any] = {"maxOutputTokens": request.max_output_tokens}
        response_format = request.metadata.get("response_format")
        if isinstance(response_format, dict):
            if response_format.get("type") == "json_object":
                generation_config["responseMimeType"] = "application/json"
            if response_format.get("json_schema"):
                generation_config["responseJsonSchema"] = response_format["json_schema"]
        payload["generationConfig"] = generation_config
        payload.update(candidate.metadata.get("extra_body", {}))

        url = f"{self._base()}/models/{self._model_name(candidate.model)}:generateContent"
        credential_env, credential_value = self.credential()
        if not credential_value:
            raise ProviderError("gemini: missing API key")
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(url, headers=self._headers(), json=payload)
        except httpx.TimeoutException as exc:
            raise ProviderError(f"{self.config.name}: request timed out") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            raise ProviderError(
                f"{self.config.name} HTTP {response.status_code}: "
                f"{redact_error(response.text[:1000])}"
            )
        data = self.decode_json(response, f"{self.config.name} completion")
        candidates = data.get("candidates") or []
        if not candidates:
            raise ProviderError(f"{self.config.name}: response had no candidates")
        selected = candidates[0]
        parts = ((selected.get("content") or {}).get("parts") or [])
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        usage = data.get("usageMetadata") or {}
        usage_reported = any(
            key in usage for key in ("promptTokenCount", "candidatesTokenCount", "totalTokenCount")
        )
        input_tokens = int(usage.get("promptTokenCount") or 0)
        output_tokens = int(usage.get("candidatesTokenCount") or 0)
        cost = None
        if candidate.input_cost_per_million is not None:
            cost = input_tokens * candidate.input_cost_per_million / 1_000_000
            if candidate.output_cost_per_million is not None:
                cost += output_tokens * candidate.output_cost_per_million / 1_000_000
        return CompletionResult(
            provider=candidate.provider,
            model=str(data.get("modelVersion") or candidate.model),
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            finish_reason=selected.get("finishReason"),
            response_id=data.get("responseId"),
            rate_limits=self.extract_rate_limits(response.headers),
            raw_usage=usage,
            usage_reported=usage_reported,
            credential_env=credential_env,
        )

    async def list_models(self) -> list[ModelCandidate]:
        found: list[ModelCandidate] = []
        page_token: str | None = None
        page_count = 0
        page_limit = self.config.catalog_page_limit
        model_limit = self.config.catalog_model_limit
        async with httpx.AsyncClient(timeout=min(self.config.timeout_seconds, 30.0)) as client:
            while page_count < page_limit and len(found) < model_limit:
                page_count += 1
                params = {"pageSize": "1000"}
                if page_token:
                    params["pageToken"] = page_token
                response = await client.get(
                    f"{self._base()}/models", headers=self._headers(), params=params
                )
                if response.status_code >= 400:
                    raise ProviderError(
                        f"{self.config.name} model discovery HTTP {response.status_code}: "
                        f"{redact_error(response.text[:500])}"
                    )
                payload = response.json()
                for item in payload.get("models") or []:
                    if len(found) >= model_limit:
                        break
                    if not isinstance(item, dict):
                        continue
                    methods = set(item.get("supportedGenerationMethods") or [])
                    if methods and "generateContent" not in methods:
                        continue
                    resource_name = str(item.get("name") or "")
                    model_id = str(item.get("baseModelId") or resource_name.removeprefix("models/"))
                    if not model_id:
                        continue
                    capabilities = {Capability.TEXT}
                    modalities = set(item.get("inputModalities") or item.get("input_modalities") or [])
                    if "IMAGE" in {str(value).upper() for value in modalities}:
                        capabilities.add(Capability.VISION)
                    if "tool" in methods or "functionCalling" in methods:
                        capabilities.add(Capability.TOOLS)
                    found.append(
                        ModelCandidate(
                            provider=self.config.name,
                            model=model_id,
                            display_name=item.get("displayName"),
                            billing_class=self.config.billing_class,
                            capabilities=capabilities,
                            service_tiers=sorted(
                                str(value) for value in (item.get("serviceTiers") or item.get("service_tiers") or [])
                            ),
                            supported_parameters=set(),
                            context_length=int(item.get("inputTokenLimit") or 8192),
                            source="live",
                            metadata={"raw": item},
                        )
                    )
                page_token = payload.get("nextPageToken")
                if not page_token:
                    break
        return found
