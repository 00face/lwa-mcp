from pathlib import Path

import pytest

from lwa_mcp.config import LoadedConfig, RouterSettings
from lwa_mcp.models import (
    BillingClass,
    Capability,
    CompletionResult,
    ConsentMode,
    ModelCandidate,
    ProviderConfig,
    TaskKind,
)
from lwa_mcp.routing import NoRouteError
from lwa_mcp.service import RouterService


def make_config(tmp_path: Path, consent: ConsentMode = ConsentMode.PAID_ONLY) -> LoadedConfig:
    providers = {}
    models = []
    for index, name in enumerate(("alpha", "beta", "gamma", "delta")):
        billing = BillingClass.PAID if name == "delta" else BillingClass.FREE_QUOTA
        providers[name] = ProviderConfig(
            name=name,
            base_url="https://example.invalid/v1",
            billing_class=billing,
            supports_live_models=False,
        )
        models.append(
            ModelCandidate(
                provider=name,
                model=f"{name}-model",
                billing_class=billing,
                capabilities={Capability.TEXT, Capability.REASONING},
                context_length=100_000,
                task_scores={
                    TaskKind.QUERY.value: 90 - index,
                    TaskKind.CONSENSUS.value: 95 - index,
                },
                input_cost_per_million=1.0 if billing == BillingClass.PAID else 0.0,
                output_cost_per_million=2.0 if billing == BillingClass.PAID else 0.0,
            )
        )
    settings = RouterSettings(
        consent_mode=consent,
        max_parallel_consensus=2,
        providers=providers,
        models=models,
    )
    return LoadedConfig(
        settings=settings,
        config_path=tmp_path / "router.yaml",
        env_path=tmp_path / "lwa.env",
        db_path=tmp_path / "lwa.sqlite3",
        tool_library_path=tmp_path / "tool-library",
    )


async def disable_refresh(service: RouterService, monkeypatch) -> None:
    async def refresh(force: bool = False):
        return {"models": len(service.catalog.all()), "refreshed": 0}

    monkeypatch.setattr(service.catalog, "refresh", refresh)


class FakeAdapter:
    def __init__(self, calls: list[tuple[str, str]], fail: bool = False):
        self.calls = calls
        self.fail = fail

    async def complete(self, candidate, request):
        self.calls.append((candidate.provider, candidate.model))
        if self.fail:
            raise RuntimeError("provider failed")
        return CompletionResult(
            provider=candidate.provider,
            model=candidate.model,
            text=f"completed by {candidate.provider}",
            input_tokens=12,
            output_tokens=8,
        )


def test_build_request_assigns_pipeline_route_intent_and_required_caps(tmp_path):
    service = RouterService(make_config(tmp_path))

    request = service.build_request(TaskKind.CONSENSUS, "Review the design", metadata={"consensus_preflight": True})
    assert request.metadata["pipeline"] == "consensus"
    assert request.metadata["route_intent"] == "consensus:free_only"
    assert request.allow_paid is False
    assert request.allow_user_pays is False
    assert request.required_capabilities == {Capability.TEXT, Capability.REASONING}

    image = service.build_request(TaskKind.IMAGE_GENERATION, "make an icon")
    assert image.metadata["pipeline"] == "image"
    assert image.metadata["route_intent"] == "image:free_only"
    assert image.required_capabilities == {Capability.IMAGE}
    assert image.metadata["aspect_ratio"] == "1:1"
    assert image.metadata["output_format"] == "png"


@pytest.mark.parametrize("task,quality", [("Provider connectivity smoke test", "balanced"), ("query", "low")])
def test_build_request_rejects_invalid_syntax_before_route_creation(tmp_path, task, quality):
    service = RouterService(make_config(tmp_path))
    with pytest.raises(ValueError):
        service.build_request(task, "smoke", quality=quality)
    usage = service.status()["usage"]
    assert usage["preflights"] == []
    assert usage["routes"] == []
    assert usage["recent"] == []


@pytest.mark.asyncio
async def test_preflight_locks_before_work_and_execution_uses_exact_route(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr("lwa_mcp.service.build_adapter", lambda cfg: FakeAdapter(calls))

    request = service.build_request(TaskKind.QUERY, "inspect this", allow_paid=False)
    prepared = await service.prepare_task(request)
    plan = prepared["preflight"]

    assert prepared["phase"] == "preflight_complete"
    assert plan["working_may_begin"] is True
    assert plan["locks"] == {
        "prompt": True,
        "token_budget": True,
        "consensus_plan": True,
        "model_routes": True,
        "dynamic_rerouting_during_work": False,
    }
    assert calls == []

    expected = (
        plan["routes"][0]["decision"]["candidate"]["provider"],
        plan["routes"][0]["decision"]["candidate"]["model"],
    )
    completed = await service.run_prepared_task(plan["plan_token"])
    assert completed["phase"] == "work_complete"
    assert calls == [expected]
    assert completed["display"]["surface"] == "LWA"
    assert "USAGE & SPEND" in completed["display"]["telemetry"]
    assert service.db.dashboard_summary()["preflights"][0]["status"] == "completed"


@pytest.mark.asyncio
async def test_reasoning_effort_is_carried_into_preflight(tmp_path):
    service = RouterService(make_config(tmp_path))
    for model in service.config.settings.models:
        model.reasoning_levels = ["instant", "medium", "high"]
    request = service.build_request(TaskKind.QUERY, "inspect this", reasoning_effort="high")
    assert request.reasoning_effort.value == "high"
    assert request.metadata["reasoning_effort"] == "high"
    prepared = await service.prepare_task(request)
    assert prepared["preflight"]["reasoning_effort"] == "high"


@pytest.mark.asyncio
async def test_preflight_does_not_trigger_live_catalog_refresh(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))

    async def fail_if_refreshed(*args, **kwargs):
        raise AssertionError("preflight must not perform live catalog discovery")

    monkeypatch.setattr(service.catalog, "refresh", fail_if_refreshed)
    prepared = await service.prepare_task(service.build_request(TaskKind.QUERY, "seed route"))

    assert prepared["phase"] == "preflight_complete"
    assert prepared["preflight"]["routes"]


@pytest.mark.asyncio
async def test_preflight_no_route_reports_unsupported_fallback_constraint(tmp_path):
    service = RouterService(make_config(tmp_path))
    request = service.build_request(
        TaskKind.QUERY,
        "inspect this",
        reasoning_effort="medium",
        allow_paid=False,
        preferred_providers=["delta", "alpha"],
    )

    with pytest.raises(NoRouteError, match="reasoning_effort=medium unsupported"):
        await service.prepare_task(request)

    assert service.status()["usage"]["preflights"] == []


@pytest.mark.asyncio
async def test_post_response_tier_guidance_is_opt_in_and_local(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    service.config.settings.post_response_tier_guidance = True
    service.config.settings.post_response_tier_guidance_mode = "local"
    await disable_refresh(service, monkeypatch)
    monkeypatch.setattr("lwa_mcp.service.build_adapter", lambda cfg: FakeAdapter([]))

    prepared = await service.prepare_task(service.build_request(TaskKind.QUERY, "tier check"))
    result = await service.run_prepared_task(prepared["preflight"]["plan_token"])
    guidance = result["next_tier_guidance"]
    assert guidance["source"] == "local"
    assert guidance["current"] == "alpha/alpha-model"
    assert guidance["accepted"] is False
    assert "fresh preflight" in guidance["directive"]


@pytest.mark.asyncio
async def test_post_response_guidance_ingests_host_suggestion_without_rerouting(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    monkeypatch.setattr("lwa_mcp.service.build_adapter", lambda cfg: FakeAdapter([]))

    prepared = await service.prepare_task(service.build_request(TaskKind.QUERY, "host suggestion"))
    result = await service.run_prepared_task(
        prepared["preflight"]["plan_token"],
        next_tier_suggestion="Use beta for the next verification run.",
    )
    guidance = result["next_tier_guidance"]
    assert guidance["source"] == "host_ingested"
    assert guidance["suggestion"].startswith("Use beta")
    assert guidance["accepted"] is False


def test_tier_guidance_setting_is_persisted(tmp_path):
    service = RouterService(make_config(tmp_path))
    assert service.set_tier_guidance(True, "codex_request") == {
        "enabled": True,
        "mode": "codex_request",
    }
    assert service._tier_guidance_enabled() is True
    assert service._tier_guidance_mode() == "codex_request"


@pytest.mark.asyncio
async def test_library_suggestions_are_evaluated_once_per_single_route_lifecycle(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    monkeypatch.setattr("lwa_mcp.service.build_adapter", lambda cfg: FakeAdapter([]))
    calls = []

    def suggest(*args, **kwargs):
        calls.append((args, kwargs))
        return [{"slug": "example"}]

    monkeypatch.setattr(service, "suggest_library_tools", suggest)
    prepared = await service.prepare_task(service.build_request(TaskKind.QUERY, "inspect this", allow_paid=False))
    completed = await service.run_prepared_task(prepared["preflight"]["plan_token"])

    assert len(calls) == 1
    assert prepared["library_suggestions"] == [{"slug": "example"}]
    assert "library_suggestions" not in completed


@pytest.mark.asyncio
async def test_prepare_task_rejects_forbidden_pipeline_metadata_before_routing(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr("lwa_mcp.service.build_adapter", lambda cfg: FakeAdapter(calls))

    request = service.build_request(
        TaskKind.IMAGE_GENERATION,
        "make a banner",
        metadata={"aspect_ratio": "16:9", "output_format": "png", "seconds": "4"},
    )
    with pytest.raises(ValueError, match="does not accept metadata keys"):
        await service.prepare_task(request)
    assert calls == []


@pytest.mark.asyncio
async def test_confirmation_happens_before_work(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path, ConsentMode.ALWAYS))
    await disable_refresh(service, monkeypatch)
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr("lwa_mcp.service.build_adapter", lambda cfg: FakeAdapter(calls))

    prepared = await service.prepare_task(service.build_request(TaskKind.QUERY, "confirm me"))
    plan = prepared["preflight"]
    assert prepared["status"] == "confirmation_required"
    assert plan["working_may_begin"] is False
    assert calls == []

    with pytest.raises(PermissionError):
        await service.run_prepared_task(plan["plan_token"])

    approved = service.approve_preflight(plan["confirmation_token"])
    assert approved["preflight"]["working_may_begin"] is True
    result = await service.run_prepared_task(plan["plan_token"])
    assert result["status"] == "completed"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_confirmation_token_is_single_use(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path, ConsentMode.ALWAYS_ASK))
    await disable_refresh(service, monkeypatch)
    prepared = await service.prepare_task(service.build_request(TaskKind.QUERY, "one use"))
    token = prepared["preflight"]["confirmation_token"]

    service.approve_preflight(token)
    with pytest.raises(ValueError, match="Unknown, expired, or already-used"):
        service.approve_preflight(token)


@pytest.mark.asyncio
async def test_expired_confirmation_token_is_rejected(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path, ConsentMode.ALWAYS_ASK))
    await disable_refresh(service, monkeypatch)
    prepared = await service.prepare_task(service.build_request(TaskKind.QUERY, "expire me"))
    plan_token = prepared["preflight"]["plan_token"]
    token = prepared["preflight"]["confirmation_token"]
    service.preflights._plans[plan_token].summary.expires_at_epoch = 0

    with pytest.raises(ValueError, match="Unknown, expired, or already-used"):
        service.approve_preflight(token)


@pytest.mark.asyncio
async def test_failure_stops_and_requires_new_preflight_without_rerouting(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr("lwa_mcp.service.build_adapter", lambda cfg: FakeAdapter(calls, fail=True))

    decide_count = 0
    original_decide = service.router.decide

    def counted(request):
        nonlocal decide_count
        decide_count += 1
        return original_decide(request)

    monkeypatch.setattr(service.router, "decide", counted)
    prepared = await service.prepare_task(
        service.build_request(TaskKind.QUERY, "must not reroute", allow_paid=False)
    )
    result = await service.run_prepared_task(prepared["preflight"]["plan_token"])

    assert result["status"] == "repreflight_required"
    assert result["phase"] == "work_stopped"
    assert decide_count == 1
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_consensus_models_and_template_are_locked_before_work(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr("lwa_mcp.service.build_adapter", lambda cfg: FakeAdapter(calls))

    prepared = await service.prepare_consensus("Review the design", voters=2, allow_paid=False)
    plan = prepared["preflight"]
    assert plan["mode"] == "consensus"
    assert plan["prompt_lock_scope"] == "template"
    assert [route["role"] for route in plan["routes"]] == [
        "consensus_voter",
        "consensus_voter",
        "consensus_voter",
        "consensus_synthesis",
    ]
    assert all(
        route["decision"]["candidate"]["billing_class"] in {"free", "free_quota"}
        for route in plan["routes"][:-1]
    )
    assert calls == []

    result = await service.run_prepared_task(plan["plan_token"])
    assert result["status"] == "completed"
    assert result["phase"] == "work_complete"
    assert len(calls) == 4


@pytest.mark.asyncio
async def test_consensus_excludes_user_pays_voters(tmp_path, monkeypatch):
    config = make_config(tmp_path)
    config.settings.providers["epsilon"] = ProviderConfig(
        name="epsilon",
        base_url="https://example.invalid/v1",
        billing_class=BillingClass.USER_PAYS,
        supports_live_models=False,
    )
    config.settings.models.append(
        ModelCandidate(
            provider="epsilon",
            model="epsilon-model",
            billing_class=BillingClass.USER_PAYS,
            capabilities={Capability.TEXT, Capability.REASONING},
            context_length=100_000,
            task_scores={TaskKind.CONSENSUS.value: 100},
        )
    )
    service = RouterService(config)
    await disable_refresh(service, monkeypatch)

    prepared = await service.prepare_consensus("Review the design", allow_paid=False)
    voters = prepared["preflight"]["routes"][:-1]
    assert voters
    assert all(route["decision"]["candidate"]["billing_class"] in {"free", "free_quota"} for route in voters)


@pytest.mark.asyncio
async def test_consensus_continues_when_one_voter_fails(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    calls: list[tuple[str, str]] = []

    def adapter_for(provider_config):
        return FakeAdapter(calls, fail=provider_config.name == "beta")

    monkeypatch.setattr("lwa_mcp.service.build_adapter", adapter_for)
    prepared = await service.prepare_consensus("Continue after one voter fails")
    result = await service.run_prepared_task(prepared["preflight"]["plan_token"])

    assert result["status"] == "completed"
    assert result["voter_failures"]
    assert result["voter_failures"][0]["provider"] == "beta"
    assert result["synthesis"]["text"]


@pytest.mark.asyncio
async def test_consensus_falls_back_when_synthesis_provider_fails(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    calls: list[tuple[str, str]] = []

    def adapter_for(provider_config):
        return FakeAdapter(calls, fail=provider_config.name == "alpha")

    monkeypatch.setattr("lwa_mcp.service.build_adapter", adapter_for)
    prepared = await service.prepare_consensus("Continue when synthesis route fails")
    result = await service.run_prepared_task(prepared["preflight"]["plan_token"])

    assert result["status"] == "completed"
    assert result["synthesis_failures"]
    assert result["synthesis_failures"][0]["provider"] == "alpha"
    assert result["synthesis"]["text"]


@pytest.mark.asyncio
async def test_consensus_compacts_long_material_before_provider_execution(tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    prompt_lengths: list[int] = []

    class LengthRecordingAdapter:
        async def complete(self, candidate, request):
            prompt_lengths.append(len(request.prompt))
            return CompletionResult(
                provider=candidate.provider,
                model=candidate.model,
                text="review " * 3_000,
                input_tokens=0,
                output_tokens=0,
            )

    monkeypatch.setattr("lwa_mcp.service.build_adapter", lambda cfg: LengthRecordingAdapter())
    prepared = await service.prepare_consensus("draft " * 20_000)
    result = await service.run_prepared_task(prepared["preflight"]["plan_token"])

    assert result["status"] == "completed"
    assert prompt_lengths
    assert max(prompt_lengths) <= 20_000

@pytest.mark.asyncio
async def test_cli_prints_preflight_before_working(tmp_path, monkeypatch, capsys):
    from lwa_mcp.cli import _finish_preflight_cli

    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr("lwa_mcp.service.build_adapter", lambda cfg: FakeAdapter(calls))

    prepared = await service.prepare_task(
        service.build_request(TaskKind.QUERY, "ordering", allow_paid=False)
    )
    result = await _finish_preflight_cli(service, prepared)
    output = capsys.readouterr().out

    assert result["status"] == "completed"
    assert output.index('"phase": "preflight_complete"') < output.index("Working...")
    assert len(calls) == 1
