from pathlib import Path

import pytest


def make_service(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("LWA_MCP_DB", str(tmp_path / "lwa.sqlite3"))
    monkeypatch.setenv("LWA_MCP_TOOL_LIBRARY", str(tmp_path / "tool-library"))
    monkeypatch.setenv("LWA_MCP_CONFIG", str(tmp_path / "router.yaml"))
    monkeypatch.setenv("LWA_MCP_ENV_FILE", str(tmp_path / "lwa.env"))
    (tmp_path / "router.yaml").write_text("providers: {}\nmodels: []\n", encoding="utf-8")
    from lwa_mcp.config import LoadedConfig, RouterSettings
    from lwa_mcp.models import (
        BillingClass,
        Capability,
        ConsentMode,
        ModelCandidate,
        ProviderConfig,
        TaskKind,
    )
    from lwa_mcp.service import RouterService

    settings = RouterSettings(
        consent_mode=ConsentMode.PAID_ONLY,
        providers={
            "mock": ProviderConfig(
                name="mock",
                api_key_env="DASHBOARD_SECRET_KEY",
                base_url="https://example.invalid/v1",
                supports_live_models=False,
                billing_class=BillingClass.FREE_QUOTA,
            )
        },
        models=[
            ModelCandidate(
                provider="mock",
                model="mock-model",
                billing_class=BillingClass.FREE_QUOTA,
                capabilities={Capability.TEXT},
                task_scores={TaskKind.QUERY.value: 90},
            )
        ],
    )
    return RouterService(
        LoadedConfig(
            settings=settings,
            config_path=tmp_path / "router.yaml",
            env_path=tmp_path / "lwa.env",
            db_path=tmp_path / "lwa.sqlite3",
            tool_library_path=tmp_path / "tool-library",
        )
    )


def test_dashboard_metadata_and_provider_payload_are_redacted(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHBOARD_SECRET_KEY", "dashboard-secret-value")
    service = make_service(tmp_path, monkeypatch)
    from lwa_mcp import dashboard

    monkeypatch.setattr(dashboard, "service", service)

    assert dashboard.app.version == "0.4.1"
    payload = dashboard.providers()
    assert payload[0]["configured"] is True
    assert "dashboard-secret-value" not in repr(payload)
    assert "api_key_env" not in repr(payload)


def test_codex_static_surface_does_not_construct_router_service(monkeypatch):
    from lwa_mcp import dashboard

    created = []

    class NeverConstructed:
        def __init__(self):
            created.append(True)

    monkeypatch.setattr(dashboard, "service", None)
    monkeypatch.setattr(dashboard, "RouterService", NeverConstructed)
    assert dashboard.codex_workspace().path.endswith("codex.html")
    assert created == []


@pytest.mark.asyncio
async def test_dashboard_status_reflects_preflight_lifecycle(tmp_path, monkeypatch):
    from lwa_mcp.models import TaskKind

    monkeypatch.setenv("DASHBOARD_SECRET_KEY", "dashboard-secret-value")
    service = make_service(tmp_path, monkeypatch)
    from lwa_mcp import dashboard

    monkeypatch.setattr(dashboard, "service", service)
    # The test asserts lifecycle metadata for an isolated service. Do not let
    # an operator-owned dashboard already listening on the default port make
    # this fixture depend on host process state.
    monkeypatch.setattr(service, "_dashboard_running", lambda host, port: False)

    prepared = await service.prepare_task(service.build_request(TaskKind.QUERY, "status check"))
    status = dashboard.status()
    assert status["consent_mode"] == "paid_only"
    assert status["dashboard_url"] == "http://127.0.0.1:8766"
    assert status["dashboard_running"] is False
    assert status["usage"]["preflights"][0]["status"] == "ready"
    assert status["usage"]["preflights"][0]["working_may_begin"] is True
    assert prepared["preflight"]["prompt_hash"] not in repr(status)


def test_dashboard_consent_endpoint_preserves_canonical_modes(tmp_path, monkeypatch):
    service = make_service(tmp_path, monkeypatch)
    from lwa_mcp import dashboard

    monkeypatch.setattr(dashboard, "service", service)

    assert dashboard.set_consent(dashboard.ConsentUpdate(mode="always")) == {"mode": "always_ask"}
    assert dashboard.set_consent(dashboard.ConsentUpdate(mode="never")) == {"mode": "automatic"}


def test_dashboard_credentials_are_masked_and_can_be_replaced_and_deleted(tmp_path, monkeypatch):
    service = make_service(tmp_path, monkeypatch)
    from lwa_mcp import dashboard

    monkeypatch.setattr(dashboard, "service", service)
    listed = dashboard.credentials()
    openrouter = next(item for item in listed if item["env_name"] == "OPENROUTER_API_KEY")
    assert openrouter["configured"] is False

    saved = dashboard.replace_credential(
        "OPENROUTER_API_KEY",
        dashboard.CredentialUpdate(value="dashboard-test-secret", confirm=True),
    )
    assert saved["credential"]["configured"] is True
    assert "dashboard-test-secret" not in repr(saved)
    assert saved["credential"]["masked"].endswith("cret")
    assert service.config.env_path.read_text(encoding="utf-8").count("OPENROUTER_API_KEY=") == 1

    deleted = dashboard.delete_credential(
        "OPENROUTER_API_KEY", dashboard.CredentialUpdate(confirm=True)
    )
    assert deleted["credential"]["configured"] is False
    assert "dashboard-test-secret" not in service.config.env_path.read_text(encoding="utf-8")


def test_dashboard_credential_mutations_require_confirmation(tmp_path, monkeypatch):
    service = make_service(tmp_path, monkeypatch)
    from fastapi import HTTPException

    from lwa_mcp import dashboard

    monkeypatch.setattr(dashboard, "service", service)
    with pytest.raises(HTTPException) as exc:
        dashboard.replace_credential(
            "OPENROUTER_API_KEY",
            dashboard.CredentialUpdate(value="not-saved", confirm=False),
        )
    assert exc.value.status_code == 400
