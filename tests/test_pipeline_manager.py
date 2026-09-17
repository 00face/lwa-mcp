import asyncio
from pathlib import Path

import pytest

from lwa_mcp.catalog import Catalog
from lwa_mcp.config import LoadedConfig, RouterSettings
from lwa_mcp.models import BillingClass, Capability, ModelCandidate, ProviderConfig, TaskKind
from lwa_mcp.pipeline_manager import PipelineManager


def make_config(tmp_path: Path) -> LoadedConfig:
    settings = RouterSettings(
        providers={
            "readybox": ProviderConfig(
                name="readybox",
                base_url="https://example.invalid/v1",
                billing_class=BillingClass.FREE_QUOTA,
                supports_live_models=False,
            ),
            "lockedbox": ProviderConfig(
                name="lockedbox",
                base_url="https://example.invalid/v1",
                api_key_env="LOCKEDBOX_KEY",
                billing_class=BillingClass.FREE_QUOTA,
                supports_live_models=False,
            ),
        },
        models=[
            ModelCandidate(
                provider="readybox",
                model="ready-model",
                billing_class=BillingClass.FREE_QUOTA,
                capabilities={Capability.TEXT},
                task_scores={TaskKind.QUERY.value: 90},
            )
        ],
    )
    return LoadedConfig(
        settings=settings,
        config_path=tmp_path / "router.yaml",
        env_path=tmp_path / "lwa.env",
        db_path=tmp_path / "lwa.sqlite3",
        tool_library_path=tmp_path / "tool-library",
    )


def test_offline_status_never_calls_provider(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    manager = PipelineManager(cfg, Catalog(cfg))
    monkeypatch.setattr(
        "lwa_mcp.pipeline_manager.build_adapter",
        lambda config: (_ for _ in ()).throw(AssertionError("offline check called adapter")),
    )

    status = manager.status("readybox")
    assert status["status"] == "ready"
    assert status["check_mode"] == "offline"
    assert status["readiness"] == "configured"
    assert status["live_verified"] is False
    assert status["quota_verified"] is False
    assert status["data_transmitted"] is False
    assert status["cost_incurred"] is False


@pytest.mark.asyncio
async def test_zero_payload_probe_does_not_create_request(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    manager = PipelineManager(cfg, Catalog(cfg))
    calls = []

    class HealthOnlyAdapter:
        async def health(self):
            calls.append("health")
            return True, "metadata endpoint reachable"

    monkeypatch.setattr("lwa_mcp.pipeline_manager.build_adapter", lambda config: HealthOnlyAdapter())
    status = await manager.check("readybox", probe=True)
    assert status["status"] == "reachable"
    assert status["check_mode"] == "zero_payload_probe"
    assert status["readiness"] == "probe_verified"
    assert status["live_verified"] is True
    assert status["data_transmitted"] is False
    assert status["cost_incurred"] is False
    assert calls == ["health"]


@pytest.mark.asyncio
async def test_success_probe_is_bounded_by_cache(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    manager = PipelineManager(cfg, Catalog(cfg))
    calls = []

    class HealthOnlyAdapter:
        async def health(self):
            calls.append("health")
            return True, "reachable"

    monkeypatch.setattr("lwa_mcp.pipeline_manager.build_adapter", lambda config: HealthOnlyAdapter())
    cold = await manager.check("readybox", probe=True)
    warm = await manager.check("readybox", probe=True)
    assert cold["cache_hit"] is False
    assert cold["network_calls"] == 1
    assert warm["cache_hit"] is True
    assert warm["network_calls"] == 0
    assert calls == ["health"]


@pytest.mark.asyncio
async def test_failed_probe_has_short_cache_and_explicit_invalidation(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    manager = PipelineManager(cfg, Catalog(cfg))
    calls = []

    class FailingAdapter:
        async def health(self):
            calls.append("health")
            raise RuntimeError("temporary outage")

    monkeypatch.setattr("lwa_mcp.pipeline_manager.build_adapter", lambda config: FailingAdapter())
    first = await manager.check("readybox", probe=True)
    second = await manager.check("readybox", probe=True)
    assert first["status"] == second["status"] == "unreachable"
    assert second["cache_hit"] is True
    assert calls == ["health"]
    assert manager.invalidate_probe_cache("readybox") == 1
    await manager.check("readybox", probe=True)
    assert calls == ["health", "health"]


@pytest.mark.asyncio
async def test_concurrent_probes_coalesce_to_one_health_call(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    manager = PipelineManager(cfg, Catalog(cfg))
    calls = []

    class SlowAdapter:
        async def health(self):
            calls.append("health")
            await asyncio.sleep(0.01)
            return True, "reachable"

    monkeypatch.setattr("lwa_mcp.pipeline_manager.build_adapter", lambda config: SlowAdapter())
    results = await asyncio.gather(
        manager.check("readybox", probe=True), manager.check("readybox", probe=True)
    )
    assert calls == ["health"]
    assert {result["status"] for result in results} == {"reachable"}


def test_missing_credentials_are_blocked_before_send(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    monkeypatch.delenv("LOCKEDBOX_KEY", raising=False)
    manager = PipelineManager(cfg, Catalog(cfg))
    assert manager.status("lockedbox")["status"] == "missing_credentials"
    with pytest.raises(Exception, match="not ready"):
        manager.assert_can_send("lockedbox")


def test_manual_pipeline_marks_are_visible(tmp_path):
    cfg = make_config(tmp_path)
    manager = PipelineManager(cfg, Catalog(cfg))
    marked = manager.mark("readybox", "maintenance", "scheduled test")
    assert marked["manual_mark"]["status"] == "maintenance"
