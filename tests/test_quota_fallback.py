import pytest

from lwa_mcp.config import LoadedConfig, RouterSettings
from lwa_mcp.models import (
    BillingClass,
    Capability,
    CompletionResult,
    ModelCandidate,
    ProviderConfig,
    TaskKind,
)
from lwa_mcp.providers.base import ProviderError
from lwa_mcp.service import RouterService


def make_config(tmp_path):
    providers = {
        name: ProviderConfig(name=name, billing_class=BillingClass.FREE_QUOTA, supports_live_models=False)
        for name in ("alpha", "beta", "gamma", "delta")
    }
    models = [
        ModelCandidate(
            provider=name,
            model=f"{name}-model",
            billing_class=BillingClass.FREE_QUOTA,
            capabilities={Capability.TEXT, Capability.REASONING},
            context_length=100_000,
            task_scores={TaskKind.QUERY.value: 90 - index},
        )
        for index, name in enumerate(providers)
    ]
    settings = RouterSettings(providers=providers, models=models)
    return LoadedConfig(
        settings=settings,
        config_path=tmp_path / "router.yaml",
        env_path=tmp_path / "lwa.env",
        db_path=tmp_path / "lwa.sqlite3",
        tool_library_path=tmp_path / "tool-library",
    )


async def disable_refresh(service, monkeypatch):
    async def refresh(force=False):
        return {"models": len(service.catalog.all()), "refreshed": 0}

    monkeypatch.setattr(service.catalog, "refresh", refresh)


@pytest.mark.asyncio
async def test_working_falls_back_only_after_authoritative_quota_error(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    request = service.build_request(
        TaskKind.QUERY,
        "quota fallback",
        preferred_providers=["alpha", "beta"],
    )
    decision = service.router.decide(request)
    calls = []

    async def execute(current_request, current_decision):
        calls.append(current_decision.candidate.provider)
        if len(calls) == 1:
            raise ProviderError("daily quota exhausted", quota_exhausted=True)
        return CompletionResult(
            provider=current_decision.candidate.provider,
            model=current_decision.candidate.model,
            text="completed",
        )

    monkeypatch.setattr(service, "execute", execute)
    result, final_decision, events = await service._execute_with_quota_fallback(request, decision)

    assert result.text == "completed"
    assert final_decision.candidate.provider == "beta"
    assert calls == ["alpha", "beta"]
    assert events[0]["reason"] == "quota_exhausted"


@pytest.mark.asyncio
async def test_working_retries_retryable_rate_limit_on_same_provider(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    request = service.build_request(TaskKind.QUERY, "temporary rate limit", preferred_providers=["alpha", "beta"])
    decision = service.router.decide(request)
    calls = []

    async def execute(current_request, current_decision):
        calls.append(current_decision.candidate.provider)
        if len(calls) == 1:
            raise ProviderError("retry later", status_code=429, retry_after_seconds=0)
        return CompletionResult(
            provider=current_decision.candidate.provider,
            model=current_decision.candidate.model,
            text="completed",
        )

    monkeypatch.setattr(service, "execute", execute)
    _result, final_decision, events = await service._execute_with_quota_fallback(request, decision)

    assert final_decision.candidate.provider == "alpha"
    assert calls == ["alpha", "alpha"]
    assert events == []
