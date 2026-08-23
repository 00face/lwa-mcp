import json
from pathlib import Path

import httpx
import pytest
import yaml

from lwa_mcp.models import (
    BillingClass,
    Capability,
    ModelCandidate,
    ProviderConfig,
    RouteRequest,
    TaskKind,
)
from lwa_mcp.providers import build_adapter
from lwa_mcp.providers.base import ProviderError
from lwa_mcp.providers.gemini import GeminiAdapter
from lwa_mcp.providers.openai_compatible import OpenAICompatibleAdapter
from lwa_mcp.providers.openai_media import OpenAIMediaAdapter
from lwa_mcp.providers.puter import PuterAdapter


def make_adapter(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    return OpenAICompatibleAdapter(
        ProviderConfig(
            name="mock",
            base_url="https://mock.invalid/v1",
            api_key_env="MOCK_API_KEY",
            supports_live_models=True,
        )
    )


def test_billing_credential_is_separate_from_generation_pool(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY_1", "free-secret")
    monkeypatch.setenv("GEMINI_BILLING_API_KEY", "billing-secret")
    adapter = GeminiAdapter(
        ProviderConfig(
            name="gemini",
            api_key_envs=["GEMINI_API_KEY_1"],
            billing_api_key_env="GEMINI_BILLING_API_KEY",
        )
    )
    assert adapter.credential() == ("GEMINI_API_KEY_1", "free-secret")
    assert adapter.credential(billing=True) == ("GEMINI_BILLING_API_KEY", "billing-secret")


@pytest.mark.asyncio
async def test_openai_compatible_completion_extracts_usage_and_rate_limits(monkeypatch):
    monkeypatch.setenv("MOCK_API_KEY", "mock-secret")

    async def handler(request):
        assert request.headers["authorization"] == "Bearer mock-secret"
        return httpx.Response(
            200,
            json={
                "id": "response-1",
                "model": "mock-model",
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 7},
            },
            headers={"x-ratelimit-remaining": "9"},
        )

    adapter = make_adapter(monkeypatch, handler)
    result = await adapter.complete(
        ModelCandidate(provider="mock", model="mock-model"),
        RouteRequest(task=TaskKind.QUERY, prompt="hello"),
    )
    assert result.text == "ok"
    assert result.input_tokens == 11
    assert result.output_tokens == 7
    assert result.usage_reported is True
    assert result.transport == "gateway"
    assert result.rate_limits["x-ratelimit-remaining"] == "9"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("effort", "wire_value"),
    [("instant", "none"), ("medium", "medium"), ("high", "high")],
)
async def test_openai_compatible_forwards_reasoning_effort(monkeypatch, effort, wire_value):
    monkeypatch.setenv("MOCK_API_KEY", "mock-secret")
    captured = {}

    async def handler(request):
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    adapter = make_adapter(monkeypatch, handler)
    await adapter.complete(
        ModelCandidate(
            provider="mock",
            model="mock-model",
            reasoning_levels=["instant", "medium", "high"],
        ),
        RouteRequest(task=TaskKind.QUERY, prompt="hello", reasoning_effort=effort),
    )
    assert captured["reasoning_effort"] == wire_value


@pytest.mark.asyncio
async def test_openai_compatible_rejects_unadvertised_reasoning_effort(monkeypatch):
    monkeypatch.setenv("MOCK_API_KEY", "mock-secret")
    adapter = make_adapter(monkeypatch, lambda request: httpx.Response(200, json={"choices": []}))
    with pytest.raises(ProviderError, match="does not advertise"):
        await adapter.complete(
            ModelCandidate(provider="mock", model="mock-model"),
            RouteRequest(task=TaskKind.QUERY, prompt="hello", reasoning_effort="high"),
        )


@pytest.mark.asyncio
async def test_openai_compatible_uses_first_available_key_pool_entry(monkeypatch):
    monkeypatch.delenv("MOCK_API_KEY", raising=False)
    monkeypatch.delenv("MOCK_KEY_ONE", raising=False)
    monkeypatch.setenv("MOCK_KEY_TWO", "pool-secret")

    async def handler(request):
        assert request.headers["authorization"] == "Bearer pool-secret"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}], "usage": {}},
        )

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    adapter = OpenAICompatibleAdapter(
        ProviderConfig(
            name="mock",
            base_url="https://mock.invalid/v1",
            api_key_envs=["MOCK_KEY_ONE", "MOCK_KEY_TWO"],
        )
    )
    result = await adapter.complete(
        ModelCandidate(provider="mock", model="mock-model"),
        RouteRequest(task=TaskKind.QUERY, prompt="hello"),
    )
    assert result.credential_env == "MOCK_KEY_TWO"


@pytest.mark.asyncio
async def test_openai_compatible_missing_usage_is_not_reported(monkeypatch):
    monkeypatch.setenv("MOCK_API_KEY", "mock-secret")

    async def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    adapter = make_adapter(monkeypatch, handler)
    result = await adapter.complete(
        ModelCandidate(provider="mock", model="mock-model"),
        RouteRequest(task=TaskKind.QUERY, prompt="hello"),
    )
    assert (result.input_tokens, result.output_tokens) == (0, 0)
    assert result.usage_reported is False


@pytest.mark.asyncio
async def test_openai_compatible_error_redacts_response_body(monkeypatch):
    monkeypatch.setenv("MOCK_API_KEY", "mock-secret")

    async def handler(request):
        return httpx.Response(401, text="invalid token mock-secret")

    adapter = make_adapter(monkeypatch, handler)
    with pytest.raises(ProviderError, match="REDACTED") as exc_info:
        await adapter.complete(
            ModelCandidate(provider="mock", model="mock-model"),
            RouteRequest(task=TaskKind.QUERY, prompt="hello"),
        )
    assert "mock-secret" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_openai_compatible_timeout_remains_bounded(monkeypatch):
    monkeypatch.setenv("MOCK_API_KEY", "mock-secret")

    async def handler(request):
        raise httpx.ReadTimeout("mock timeout")

    adapter = make_adapter(monkeypatch, handler)
    with pytest.raises(ProviderError, match="request timed out"):
        await adapter.complete(
            ModelCandidate(provider="mock", model="mock-model"),
            RouteRequest(task=TaskKind.QUERY, prompt="hello"),
        )


@pytest.mark.asyncio
async def test_openai_compatible_malformed_response_is_normalized(monkeypatch):
    monkeypatch.setenv("MOCK_API_KEY", "mock-secret")

    async def handler(request):
        return httpx.Response(200, text="not-json")

    adapter = make_adapter(monkeypatch, handler)
    with pytest.raises(ProviderError, match="malformed JSON response"):
        await adapter.complete(
            ModelCandidate(provider="mock", model="mock-model"),
            RouteRequest(task=TaskKind.QUERY, prompt="hello"),
        )


@pytest.mark.asyncio
async def test_openai_compatible_rejects_unadvertised_response_format(monkeypatch):
    monkeypatch.setenv("MOCK_API_KEY", "mock-secret")

    async def handler(request):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}], "usage": {}},
        )

    adapter = make_adapter(monkeypatch, handler)
    with pytest.raises(ProviderError, match="does not advertise response_format support"):
        await adapter.complete(
            ModelCandidate(
                provider="mock",
                model="mock-model",
                supported_parameters={"tools"},
            ),
            RouteRequest(
                task=TaskKind.QUERY,
                prompt="hello",
                metadata={"response_format": {"type": "json_object"}},
            ),
        )


@pytest.mark.asyncio
async def test_streaming_is_explicitly_rejected_by_baseline_adapter(monkeypatch):
    adapter = OpenAICompatibleAdapter(ProviderConfig(name="mock"))
    with pytest.raises(ProviderError, match="streaming is not supported"):
        await adapter.stream(
            ModelCandidate(provider="mock", model="mock-model"),
            RouteRequest(task=TaskKind.QUERY, prompt="hello"),
        )


@pytest.mark.asyncio
async def test_model_discovery_marks_zero_cost_models_free(monkeypatch):
    async def handler(request):
        return httpx.Response(
            200,
            json={"data": [{"id": "free-model", "pricing": {"prompt": 0, "completion": 0}}]},
        )

    adapter = make_adapter(monkeypatch, handler)
    models = await adapter.list_models()
    assert models[0].billing_class is BillingClass.FREE


@pytest.mark.asyncio
async def test_puter_discovery_uses_documented_native_listing_source(monkeypatch):
    monkeypatch.setenv("PUTER_AUTH_TOKEN", "puter-secret")

    async def handler(request):
        assert request.url.path == "/puterai/chat/models/details"
        assert request.headers["authorization"] == "Bearer puter-secret"
        return httpx.Response(
            200,
            json={"models": [{"id": "puter-model", "provider": "puter", "name": "Puter Model"}]},
        )

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    adapter = PuterAdapter(
        ProviderConfig(
            name="puter",
            adapter="puter",
            base_url="https://api.puter.com/puterai/openai/v1",
            api_key_env="PUTER_AUTH_TOKEN",
        )
    )
    models = await adapter.list_models()
    assert models[0].model == "puter-model"
    assert models[0].provider == "puter"


def test_structured_secret_parameters_are_redacted(monkeypatch):
    from lwa_mcp.providers.base import redact_error

    safe = redact_error("provider returned?api_key=abc123&token=xyz789")
    assert "abc123" not in safe
    assert "xyz789" not in safe


@pytest.mark.asyncio
async def test_openai_media_image_saves_official_image_response(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")
    monkeypatch.setattr("lwa_mcp.providers.openai_media.STATE_DIR", tmp_path)

    async def handler(request):
        assert request.headers["authorization"] == "Bearer openai-secret"
        assert request.url.path == "/v1/images/generations"
        payload = await request.aread()
        assert b"gpt-image-1" in payload
        return httpx.Response(
            200,
            json={"data": [{"b64_json": "aGVsbG8="}]},
        )

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    adapter = OpenAIMediaAdapter(
        ProviderConfig(
            name="openai",
            adapter="openai_media",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
        )
    )
    result = await adapter.complete(
        ModelCandidate(provider="openai", model="gpt-image-1", capabilities={Capability.IMAGE}),
        RouteRequest(task=TaskKind.IMAGE_GENERATION, prompt="a test image"),
    )
    output = Path(result.text)
    assert output.read_bytes() == b"hello"


@pytest.mark.asyncio
async def test_gemini_native_completion_and_model_discovery(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-secret")
    calls: list[httpx.Request] = []

    async def handler(request):
        calls.append(request)
        assert request.headers["x-goog-api-key"] == "gemini-secret"
        if request.url.path.endswith("/models"):
            return httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "name": "models/gemini-2.5-flash",
                            "baseModelId": "gemini-2.5-flash",
                            "displayName": "Gemini 2.5 Flash",
                            "inputTokenLimit": 1048576,
                            "supportedGenerationMethods": ["generateContent"],
                        }
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "responseId": "gemini-response",
                "modelVersion": "gemini-2.5-flash-001",
                "candidates": [{"content": {"parts": [{"text": "ok"}]}, "finishReason": "STOP"}],
                "usageMetadata": {"promptTokenCount": 11, "candidatesTokenCount": 7},
            },
        )

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    adapter = GeminiAdapter(
        ProviderConfig(
            name="gemini",
            adapter="gemini",
            base_url="https://generativelanguage.googleapis.com/v1beta",
            api_key_env="GEMINI_API_KEY",
            billing_class=BillingClass.FREE_QUOTA,
        )
    )
    models = await adapter.list_models()
    result = await adapter.complete(
        models[0], RouteRequest(task=TaskKind.QUERY, prompt="hello", system_prompt="be brief")
    )
    assert result.text == "ok"
    assert result.input_tokens == 11
    assert result.output_tokens == 7
    assert result.usage_reported is True
    assert result.credential_env == "GEMINI_API_KEY"
    assert len(calls) == 2
    assert "gemini-secret" not in str(calls[1].url)


def test_default_provider_matrix_covers_required_pipelines():
    data = yaml.safe_load(
        Path("src/lwa_mcp/defaults/router.example.yaml").read_text(encoding="utf-8")
    )
    providers = data["providers"]
    required = {
        "gemini", "openai", "openrouter", "groq", "mistral", "cloudflare", "siliconflow", "venice",
        "pollinations", "cohere", "replicate", "stability", "nvidia", "zai",
        "aion", "zenmux", "cerebras", "blackbox", "puter",
    }
    assert required <= providers.keys()
    assert providers["puter"]["billing_class"] == "user_pays"


def test_all_configured_provider_adapters_construct_offline():
    data = yaml.safe_load(
        Path("src/lwa_mcp/defaults/router.example.yaml").read_text(encoding="utf-8")
    )
    providers = data["providers"]
    adapters = [
        build_adapter(ProviderConfig.model_validate({"name": name, **spec}))
        for name, spec in providers.items()
    ]
    assert len(adapters) == 19
    assert {adapter.config.name for adapter in adapters} == set(providers)
