
import stat

from lwa_mcp.config import (
    LoadedConfig,
    RouterSettings,
    install_default_config,
    load_config,
    save_settings,
)
from lwa_mcp.models import ConsentMode, parse_consent_mode


def test_packaged_default_can_install(tmp_path, monkeypatch):
    from lwa_mcp import config

    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path / "config")
    monkeypatch.setattr(config, "DEFAULT_CONFIG_FILE", tmp_path / "config" / "router.yaml")
    path = install_default_config()
    assert path.exists()
    text = path.read_text()
    assert "openrouter:" in text
    assert "gemini:" in text
    assert "openai:" in text
    assert "puter:" in text


def test_consent_mode_aliases_are_accepted():
    assert parse_consent_mode("always") is ConsentMode.ALWAYS_ASK
    assert parse_consent_mode("always_ask") is ConsentMode.ALWAYS_ASK
    assert parse_consent_mode("automatic") is ConsentMode.AUTOMATIC
    assert parse_consent_mode("never") is ConsentMode.AUTOMATIC


def test_load_config_installs_missing_explicit_config_path(tmp_path, monkeypatch):
    config_path = tmp_path / "custom" / "router.yaml"
    monkeypatch.setenv("LWA_MCP_CONFIG", str(config_path))
    monkeypatch.setenv("LWA_MCP_ENV_FILE", str(tmp_path / "state" / "lwa.env"))
    monkeypatch.setenv("LWA_MCP_DB", str(tmp_path / "state" / "lwa.sqlite3"))
    monkeypatch.setenv("LWA_MCP_TOOL_LIBRARY", str(tmp_path / "data" / "tool-library"))

    loaded = load_config()

    assert loaded.config_path == config_path
    assert config_path.exists()
    assert "openrouter:" in config_path.read_text(encoding="utf-8")


def test_save_settings_protects_config_directory(tmp_path):
    config_dir = tmp_path / "config"
    config = LoadedConfig(
        settings=RouterSettings(),
        config_path=config_dir / "router.yaml",
        env_path=tmp_path / "state" / "lwa.env",
        db_path=tmp_path / "state" / "lwa.sqlite3",
        tool_library_path=tmp_path / "data" / "tool-library",
    )
    save_settings(config, config.settings)
    assert stat.S_IMODE(config_dir.stat().st_mode) == 0o700


def test_provider_experimental_and_model_disabled_metadata_are_configurable():
    from lwa_mcp.models import BillingClass, Capability, ModelCandidate, ProviderConfig

    provider = ProviderConfig(
        name="brokenbox",
        experimental=True,
        enabled=False,
        disabled_reason="verification required",
        billing_class=BillingClass.FREE_QUOTA,
    )
    model = ModelCandidate(
        provider="brokenbox",
        model="seed-model",
        enabled=False,
        disabled_reason="verification required",
        capabilities={Capability.TEXT},
    )

    assert provider.experimental is True
    assert provider.enabled is False
    assert model.enabled is False
    assert model.disabled_reason == "verification required"
