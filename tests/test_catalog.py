from pathlib import Path

import pytest

from lwa_mcp.catalog import Catalog
from lwa_mcp.config import LoadedConfig, RouterSettings
from lwa_mcp.models import BillingClass, Capability, ModelCandidate, ProviderConfig


def make_config(tmp_path: Path) -> LoadedConfig:
    return LoadedConfig(
        settings=RouterSettings(
            providers={
                "brokenbox": ProviderConfig(
                    name="brokenbox",
                    api_key_env="BROKENBOX_KEY",
                    billing_class=BillingClass.FREE_QUOTA,
                )
            },
            models=[
                ModelCandidate(
                    provider="brokenbox",
                    model="seed-model",
                    billing_class=BillingClass.FREE_QUOTA,
                    capabilities={Capability.TEXT},
                )
            ],
        ),
        config_path=tmp_path / "router.yaml",
        env_path=tmp_path / "lwa.env",
        db_path=tmp_path / "lwa.sqlite3",
        tool_library_path=tmp_path / "tool-library",
    )


@pytest.mark.asyncio
async def test_first_discovery_error_disables_unverified_seed_models(tmp_path, monkeypatch):
    cfg = make_config(tmp_path)
    monkeypatch.setenv("BROKENBOX_KEY", "present-but-not-disclosed")

    class FailingAdapter:
        async def list_models(self):
            raise RuntimeError("brokenbox model discovery HTTP 401")

    monkeypatch.setattr("lwa_mcp.catalog.build_adapter", lambda config: FailingAdapter())

    catalog = Catalog(cfg)
    result = await catalog.refresh(force=True)

    model = catalog.all()[0]
    health = catalog.health["brokenbox"]
    assert result == {"models": 1, "refreshed": 0}
    assert model.enabled is False
    assert "Experimental provider" in model.disabled_reason
    assert cfg.settings.providers["brokenbox"].experimental is True
    assert health.experimental is True
    assert health.healthy is False
    assert "HTTP 401" in health.detail


@pytest.mark.asyncio
async def test_configured_provider_without_error_remains_unverified_not_experimental(tmp_path, monkeypatch):
    cfg = make_config(tmp_path)
    monkeypatch.setenv("BROKENBOX_KEY", "present-but-not-disclosed")

    class EmptyAdapter:
        async def list_models(self):
            return []

    monkeypatch.setattr("lwa_mcp.catalog.build_adapter", lambda config: EmptyAdapter())

    catalog = Catalog(cfg)
    await catalog.refresh(force=True)

    model = catalog.all()[0]
    health = catalog.health["brokenbox"]
    assert model.enabled is True
    assert cfg.settings.providers["brokenbox"].experimental is False
    assert health.healthy is True
    assert health.experimental is False
