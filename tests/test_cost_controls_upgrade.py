from pathlib import Path

import pytest

from lwa_mcp.models import TaskKind
from lwa_mcp.service import RouterService, compact_prompt_material
from tests.test_preflight import disable_refresh, make_config


def test_adaptive_policy_classifies_routine_and_high_risk_requests(tmp_path: Path):
    service = RouterService(make_config(tmp_path))
    routine = service.build_request(TaskKind.QUERY, "Fix the typo in this sentence")
    high_risk = service.build_request(TaskKind.CODING_AUX, "Review this security vulnerability and migration")

    assert service.consensus_policy_for(routine)["enabled"] is False
    assert service.consensus_policy_for(high_risk)["enabled"] is True
    assert service.consensus_policy_for(high_risk)["source"] == "adaptive"


def test_explicit_consensus_override_beats_adaptive_policy(tmp_path: Path):
    service = RouterService(make_config(tmp_path))
    request = service.build_request(TaskKind.QUERY, "Fix the typo")

    service.set_consensus_default(True)
    decision = service.consensus_policy_for(request)

    assert decision["enabled"] is True
    assert decision["source"] == "session_override"
    assert decision["override"] is True


@pytest.mark.asyncio
async def test_consensus_preflight_defaults_to_two_voters(tmp_path: Path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)

    prepared = await service.prepare_consensus("Review this design")

    assert len(prepared["preflight"]["routes"]) == 3
    assert prepared["preflight"]["locks"]["consensus_quorum"] is True


@pytest.mark.asyncio
async def test_shared_prepare_prompt_applies_adaptive_policy_and_budget(tmp_path: Path, monkeypatch):
    config = make_config(tmp_path)
    config.settings.session_token_ceiling = 2_000
    service = RouterService(config)
    await disable_refresh(service, monkeypatch)

    request = service.build_request(TaskKind.QUERY, "Fix a typo", max_output_tokens=1_200)
    prepared = await service.prepare_prompt(request)

    assert prepared["preflight"]["mode"] == "single"
    assert prepared["preflight"]["consensus_policy"]["enabled"] is False
    assert prepared["session_budget"]["mode"] == "economy"
    assert prepared["preflight"]["max_output_tokens"] <= config.settings.economy_output_tokens


def test_context_compaction_removes_repeated_tool_output():
    material = "TOOL OUTPUT:\nunchanged result\n" * 20 + "FINAL REQUEST: keep this"

    compacted = compact_prompt_material(material, limit=240)

    assert len(compacted) <= 240
    assert "FINAL REQUEST: keep this" in compacted
    assert "repeated tool output removed" in compacted


def test_task_aware_auxiliary_routing_prefers_third_party(tmp_path: Path):
    service = RouterService(make_config(tmp_path))

    order = service.task_provider_order(TaskKind.CONVERSATION_COMPRESSION)

    assert order
    assert order[0] != "codex"


def test_session_token_ceiling_reports_warning_and_blocks_overage(tmp_path: Path):
    config = make_config(tmp_path)
    config.settings.session_token_ceiling = 100
    config.settings.session_token_warning_thresholds = [0.5, 0.8, 1.0]
    service = RouterService(config)

    first = service.reserve_session_tokens(60)
    second = service.reserve_session_tokens(50)

    assert first["status"] == "warning"
    assert first["mode"] == "economy"
    assert second["status"] == "blocked"
    assert second["fallback"] == "single_route"


@pytest.mark.asyncio
async def test_consensus_skips_synthesis_when_voters_agree(tmp_path: Path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)
    prepared = await service.prepare_consensus("Review this design")
    calls = []

    async def execute(request, decision):
        calls.append(decision.candidate.provider)
        from lwa_mcp.models import CompletionResult

        return CompletionResult(
            provider=decision.candidate.provider,
            model=decision.candidate.model,
            text="same short answer",
        )

    monkeypatch.setattr(service, "execute", execute)
    result = await service.run_prepared_task(prepared["preflight"]["plan_token"])

    assert result["synthesis_skipped"] is True
    assert result["synthesis"]["text"] == "same short answer"
    assert len(calls) == 2
