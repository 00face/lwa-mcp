from pathlib import Path

import pytest

from lwa_mcp.catalog import Catalog
from lwa_mcp.config import LoadedConfig, RouterSettings
from lwa_mcp.consent import ConsentGate
from lwa_mcp.db import UsageDB
from lwa_mcp.models import (
    BillingClass,
    Capability,
    CompletionResult,
    ConsentMode,
    ModelCandidate,
    ProviderConfig,
    ProviderHealth,
    RouteRequest,
    TaskKind,
)
from lwa_mcp.providers.base import redact_error
from lwa_mcp.routing import NoRouteError, Router


def make_config(tmp_path: Path, consent=ConsentMode.PAID_ONLY) -> LoadedConfig:
    settings = RouterSettings(
        consent_mode=consent,
        providers={
            "freebox": ProviderConfig(
                name="freebox", api_key_env="FREEBOX_KEY", base_url="https://example.invalid/v1",
                billing_class=BillingClass.FREE_QUOTA,
            ),
            "probox": ProviderConfig(
                name="probox", api_key_env="PROBOX_KEY", base_url="https://example.invalid/v1",
                billing_class=BillingClass.PAID, monthly_usd_cap=10,
            ),
        },
        models=[
            ModelCandidate(
                provider="freebox", model="free-model", billing_class=BillingClass.FREE_QUOTA,
                capabilities={Capability.TEXT}, context_length=100_000,
                task_scores={TaskKind.CODING_AUX.value: 90},
            ),
            ModelCandidate(
                provider="probox", model="pro-model", billing_class=BillingClass.PAID,
                capabilities={Capability.TEXT}, context_length=100_000,
                task_scores={TaskKind.CODING_AUX.value: 100},
                input_cost_per_million=2.0, output_cost_per_million=8.0,
            ),
        ],
    )
    return LoadedConfig(
        settings=settings,
        config_path=tmp_path / "router.yaml",
        env_path=tmp_path / "keys.env",
        db_path=tmp_path / "lwa.sqlite3",
        tool_library_path=tmp_path / "tool-library",
    )


def request(quality: str) -> RouteRequest:
    return RouteRequest(task=TaskKind.CODING_AUX, prompt="review this patch", quality=quality)


def test_economy_prefers_free_and_high_can_escalate(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    monkeypatch.setenv("PROBOX_KEY", "x")
    cfg = make_config(tmp_path)
    cfg.settings.allow_paid = True
    db = UsageDB(cfg.db_path)
    router = Router(cfg, Catalog(cfg), db)

    economy = router.decide(request("economy"))
    assert economy.candidate.provider == "freebox"
    assert economy.requires_confirmation is False

    high = router.decide(request("high").model_copy(update={"allow_paid": True}))
    assert high.candidate.provider == "probox"
    assert high.requires_confirmation is True


def test_allow_paid_false_excludes_pro(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    monkeypatch.setenv("PROBOX_KEY", "x")
    cfg = make_config(tmp_path)
    cfg.settings.allow_paid = True
    router = Router(cfg, Catalog(cfg), UsageDB(cfg.db_path))
    req = request("high").model_copy(update={"allow_paid": False})
    assert router.decide(req).candidate.provider == "freebox"


def test_explicit_provider_order_beats_score_but_skips_ineligible_first_choice(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    monkeypatch.setenv("PROBOX_KEY", "x")
    cfg = make_config(tmp_path, ConsentMode.NEVER)
    cfg.settings.allow_paid = True
    router = Router(cfg, Catalog(cfg), UsageDB(cfg.db_path))

    preferred_free = request("balanced").model_copy(
        update={"preferred_providers": ["freebox", "probox"], "allow_paid": True}
    )
    assert router.decide(preferred_free).candidate.provider == "freebox"

    free_only = preferred_free.model_copy(update={"allow_paid": False})
    assert router.decide(free_only).candidate.provider == "freebox"


def test_no_route_error_identifies_each_blocking_gate(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    monkeypatch.setenv("PROBOX_KEY", "x")
    cfg = make_config(tmp_path, ConsentMode.NEVER)
    cfg.settings.allow_paid = True
    cfg.settings.models[0].reasoning_levels = ["instant"]
    cfg.settings.models[1].reasoning_levels = ["high"]
    router = Router(cfg, Catalog(cfg), UsageDB(cfg.db_path))
    req = request("balanced").model_copy(
        update={
            "reasoning_effort": "high",
            "allow_paid": False,
            "preferred_providers": ["probox", "freebox"],
        }
    )

    with pytest.raises(NoRouteError) as caught:
        router.decide(req)

    message = str(caught.value)
    assert "probox/pro-model" in message
    assert "paid route disabled" in message
    assert "freebox/free-model" in message
    assert "reasoning_effort=high unsupported" in message


def test_equal_scores_use_a_deterministic_provider_and_model_order(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    monkeypatch.setenv("ALPHABOX_KEY", "x")
    cfg = make_config(tmp_path)
    cfg.settings.providers["alphabox"] = ProviderConfig(
        name="alphabox",
        api_key_env="ALPHABOX_KEY",
        base_url="https://example.invalid/v1",
        billing_class=BillingClass.FREE_QUOTA,
    )
    cfg.settings.models.append(
        ModelCandidate(
            provider="alphabox",
            model="same-score-model",
            billing_class=BillingClass.FREE_QUOTA,
            capabilities={Capability.TEXT},
            context_length=100_000,
            task_scores={TaskKind.CODING_AUX.value: 90},
        )
    )
    decision = Router(cfg, Catalog(cfg), UsageDB(cfg.db_path)).decide(request("balanced"))
    assert decision.candidate.provider == "alphabox"


def test_user_pays_is_excluded_unless_explicitly_allowed(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    monkeypatch.setenv("PUTER_KEY", "x")
    cfg = make_config(tmp_path)
    cfg.settings.allow_user_pays = True
    cfg.settings.providers["puter"] = ProviderConfig(
        name="puter",
        api_key_env="PUTER_KEY",
        base_url="https://example.invalid/v1",
        billing_class=BillingClass.USER_PAYS,
    )
    cfg.settings.models.append(
        ModelCandidate(
            provider="puter",
            model="gpt-5.6-sol",
            billing_class=BillingClass.USER_PAYS,
            capabilities={Capability.TEXT},
            context_length=100_000,
            task_scores={TaskKind.SITREP.value: 100},
        )
    )
    router = Router(cfg, Catalog(cfg), UsageDB(cfg.db_path))
    req = RouteRequest(task=TaskKind.SITREP, prompt="Write a SITREP", quality="high")
    assert router.decide(req).candidate.provider == "freebox"
    approved = req.model_copy(update={"allow_user_pays": True})
    assert router.decide(approved).candidate.provider == "puter"


def test_live_unhealthy_provider_seed_models_are_gated(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    monkeypatch.setenv("PROBOX_KEY", "x")
    cfg = make_config(tmp_path)
    cfg.settings.allow_paid = True
    catalog = Catalog(cfg)
    catalog.health["freebox"] = ProviderHealth(
        provider="freebox",
        configured=True,
        enabled=True,
        healthy=False,
        detail="model discovery HTTP 401",
    )
    router = Router(cfg, catalog, UsageDB(cfg.db_path))
    decision = router.decide(request("economy").model_copy(update={"allow_paid": True}))
    assert decision.candidate.provider == "probox"


def test_missing_key_excludes_provider(tmp_path, monkeypatch):
    monkeypatch.delenv("FREEBOX_KEY", raising=False)
    monkeypatch.setenv("PROBOX_KEY", "x")
    cfg = make_config(tmp_path, ConsentMode.NEVER)
    cfg.settings.allow_paid = True
    decision = Router(cfg, Catalog(cfg), UsageDB(cfg.db_path)).decide(
        request("economy").model_copy(update={"allow_paid": True})
    )
    assert decision.candidate.provider == "probox"


def test_router_skips_models_that_do_not_advertise_requested_parameters(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    cfg = make_config(tmp_path, ConsentMode.NEVER)
    cfg.settings.allow_paid = True
    cfg.settings.models[0].supported_parameters = {"tools"}
    router = Router(cfg, Catalog(cfg), UsageDB(cfg.db_path))
    req = request("balanced").model_copy(
        update={"metadata": {"response_format": {"type": "json_object"}}}
    )
    with pytest.raises(RuntimeError, match="No configured model"):
        router.decide(req)


def test_router_requires_a_model_to_advertise_requested_reasoning_effort(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    cfg = make_config(tmp_path, ConsentMode.NEVER)
    cfg.settings.models[0].reasoning_levels = ["instant", "medium"]
    router = Router(cfg, Catalog(cfg), UsageDB(cfg.db_path))
    high = request("balanced").model_copy(update={"reasoning_effort": "high"})
    with pytest.raises(RuntimeError, match="No configured model"):
        router.decide(high)

    medium = high.model_copy(update={"reasoning_effort": "medium"})
    assert router.decide(medium).candidate.provider == "freebox"


def test_daily_cap_removes_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    monkeypatch.setenv("PROBOX_KEY", "x")
    cfg = make_config(tmp_path, ConsentMode.NEVER)
    cfg.settings.allow_paid = True
    cfg.settings.providers["freebox"].daily_request_cap = 1
    db = UsageDB(cfg.db_path)
    router = Router(cfg, Catalog(cfg), db)
    req = request("economy").model_copy(update={"allow_paid": True})
    first = router.decide(req)
    db.record_result(req, first, CompletionResult(provider="freebox", model="free-model", text="ok"), "ok")
    second = router.decide(req)
    assert second.candidate.provider == "probox"


def test_consent_tokens_are_single_use(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    monkeypatch.setenv("PROBOX_KEY", "x")
    cfg = make_config(tmp_path, ConsentMode.ALWAYS)
    decision = Router(cfg, Catalog(cfg), UsageDB(cfg.db_path)).decide(request("economy"))
    gate = ConsentGate(ttl_seconds=60)
    token = gate.issue(request("economy"), decision)
    assert gate.consume(token).decision.candidate.provider == "freebox"
    with pytest.raises(ValueError):
        gate.consume(token)


def test_provider_error_redacts_credentials(monkeypatch):
    monkeypatch.setenv("TEST_PROVIDER_API_KEY", "secret-value-123")
    safe = redact_error("Bearer secret-value-123 returned secret-value-123")
    assert "secret-value-123" not in safe
    assert "[REDACTED]" in safe
