from pathlib import Path

import pytest

from lwa_mcp.catalog import Catalog
from lwa_mcp.config import LoadedConfig, RouterSettings
from lwa_mcp.db import UsageDB
from lwa_mcp.models import (
    BillingClass,
    Capability,
    ModelCandidate,
    ProviderConfig,
    RouteRequest,
    TaskKind,
)
from lwa_mcp.routing import NoRouteError, Router


def test_router_settings_expose_named_provider_modes():
    settings = RouterSettings.model_validate({
        "routing": {
            "mode": "third_party_first",
            "routes": {"third_party_first": ["freebox", "probox"]},
        }
    })
    assert settings.routing.mode.value == "third_party_first"
    assert settings.routing.routes["third_party_first"] == ["freebox", "probox"]


def test_policy_order_precedes_score_when_request_has_no_explicit_order(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    monkeypatch.setenv("PROBOX_KEY", "x")
    settings = RouterSettings(
        routing={"mode": "third_party_first", "routes": {"third_party_first": ["freebox", "probox"]}},
        providers={
            "freebox": ProviderConfig(name="freebox", api_key_env="FREEBOX_KEY", billing_class=BillingClass.FREE_QUOTA),
            "probox": ProviderConfig(name="probox", api_key_env="PROBOX_KEY", billing_class=BillingClass.PAID),
        },
        models=[
            ModelCandidate(provider="freebox", model="free", capabilities={Capability.TEXT}, task_scores={"query": 40}),
            ModelCandidate(provider="probox", model="pro", capabilities={Capability.TEXT}, task_scores={"query": 100}),
        ],
    )
    config = LoadedConfig(settings=settings, config_path=tmp_path / "r.yaml", env_path=tmp_path / "e", db_path=tmp_path / "d.sqlite", tool_library_path=tmp_path / "tools")
    decision = Router(config, Catalog(config), UsageDB(config.db_path)).decide(RouteRequest(task=TaskKind.QUERY, prompt="question", allow_paid=True))
    assert decision.candidate.provider == "freebox"


def test_router_restores_persisted_mode_and_manual_provider(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    settings = RouterSettings(
        providers={
            "freebox": ProviderConfig(name="freebox", api_key_env="FREEBOX_KEY", billing_class=BillingClass.FREE_QUOTA),
            "probox": ProviderConfig(name="probox", api_key_env="FREEBOX_KEY", billing_class=BillingClass.FREE_QUOTA),
        },
        models=[
            ModelCandidate(provider="freebox", model="free", task_scores={"query": 100}),
            ModelCandidate(provider="probox", model="pro", task_scores={"query": 1}),
        ],
    )
    config = LoadedConfig(
        settings=settings,
        config_path=tmp_path / "r.yaml",
        env_path=tmp_path / "e",
        db_path=tmp_path / "d.sqlite",
        tool_library_path=tmp_path / "tools",
    )
    db = UsageDB(config.db_path)
    db.set_setting("routing_mode", "manual")
    db.set_setting("manual_provider", "probox")

    router = Router(config, Catalog(config), db)
    assert router.routing_policy().mode.value == "manual"
    assert router.routing_policy().manual_provider == "probox"
    assert router.decide(RouteRequest(task=TaskKind.QUERY, prompt="question")).candidate.provider == "probox"


def test_manual_mode_without_provider_has_no_route(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("FREEBOX_KEY", "x")
    settings = RouterSettings(
        providers={"freebox": ProviderConfig(name="freebox", api_key_env="FREEBOX_KEY")},
        models=[ModelCandidate(provider="freebox", model="free")],
    )
    config = LoadedConfig(
        settings=settings,
        config_path=tmp_path / "r.yaml",
        env_path=tmp_path / "e",
        db_path=tmp_path / "d.sqlite",
        tool_library_path=tmp_path / "tools",
    )
    db = UsageDB(config.db_path)
    db.set_setting("routing_mode", "manual")
    router = Router(config, Catalog(config), db)

    with pytest.raises(NoRouteError):
        router.decide(RouteRequest(task=TaskKind.QUERY, prompt="question"))
