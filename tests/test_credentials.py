import io
import stat

from dotenv import dotenv_values

from lwa_mcp.credentials import (
    CREDENTIAL_SPECS,
    discover_credentials,
    run_credential_wizard,
    write_env_securely,
)


def test_secure_env_write_preserves_exact_value(tmp_path):
    env_path = tmp_path / "state" / "lwa.env"
    value = "sk-visible-${HOME}-with'quote\\tail"
    write_env_securely({"OPENROUTER_API_KEY": value}, env_path)

    parsed = dotenv_values(env_path, interpolate=False)
    assert parsed["OPENROUTER_API_KEY"] == value
    assert stat.S_IMODE(env_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(env_path.parent.stat().st_mode) == 0o700


def test_discovers_codex_provider_env_reference(tmp_path, monkeypatch):
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text(
        """
[model_providers.openrouter_aux]
name = "OpenRouter auxiliary"
base_url = "https://openrouter.ai/api/v1"
env_key = "MY_CODEX_OPENROUTER_KEY"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    monkeypatch.setenv("MY_CODEX_OPENROUTER_KEY", "codex-discovered-key")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    found = discover_credentials(tmp_path / "lwa.env", cwd=tmp_path)
    assert found["OPENROUTER_API_KEY"].value == "codex-discovered-key"
    assert "Codex config provider" in found["OPENROUTER_API_KEY"].source


def test_visible_wizard_confirms_and_saves(tmp_path, monkeypatch):
    from lwa_mcp import credentials

    state_dir = tmp_path / "state"
    env_path = state_dir / "lwa.env"
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    monkeypatch.setattr(credentials, "STATE_DIR", state_dir)
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_KEY", raising=False)

    answers = iter(["", "sk-user-can-see-this", ""])
    prompts: list[str] = []

    def visible_input(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers)

    output = io.StringIO()
    result = run_credential_wizard(
        env_path,
        specs=(CREDENTIAL_SPECS[0],),
        input_func=visible_input,
        output=output,
        stdin_is_tty=True,
    )

    assert result["status"] == "completed"
    assert (
        dotenv_values(env_path, interpolate=False)["OPENROUTER_API_KEY"]
        == "sk-user-can-see-this"
    )
    assert "Confirm exact value: OPENROUTER_API_KEY=sk-user-can-see-this" in output.getvalue()
    assert any("visible; Enter to skip" in prompt for prompt in prompts)
    assert stat.S_IMODE(env_path.stat().st_mode) == 0o600


def test_first_run_reopens_when_required_gemini_key_is_missing(tmp_path):
    from lwa_mcp import credentials

    env_path = tmp_path / "state" / "lwa.env"
    credentials.write_env_securely({"OPENROUTER_API_KEY": "existing"}, env_path)
    marker = env_path.parent / ".credential-wizard-complete"
    marker.write_text("completed\n", encoding="utf-8")
    gemini = next(spec for spec in CREDENTIAL_SPECS if spec.env_name == "GEMINI_API_KEY")
    answers = iter(["", "gemini-value", ""])

    result = run_credential_wizard(
        env_path,
        first_run=True,
        specs=(gemini,),
        input_func=lambda prompt: next(answers),
        stdin_is_tty=True,
    )

    assert result["status"] == "completed"
    assert dotenv_values(env_path, interpolate=False)["GEMINI_API_KEY"] == "gemini-value"


def test_wizard_no_longer_includes_bingart(tmp_path):
    assert all(spec.env_name != "BING_COOKIE_U" for spec in CREDENTIAL_SPECS)
