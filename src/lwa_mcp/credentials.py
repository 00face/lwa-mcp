from __future__ import annotations

import os
import re
import stat
import sys
import tomllib
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import TextIO

from dotenv import dotenv_values

from .config import DEFAULT_ENV_FILE, STATE_DIR  # noqa: F401 - compatibility export


@dataclass(frozen=True)
class CredentialSpec:
    env_name: str
    provider: str
    label: str
    aliases: tuple[str, ...] = ()
    optional: bool = False
    warning: str = ""


@dataclass(frozen=True)
class DiscoveredCredential:
    env_name: str
    value: str
    source: str


CREDENTIAL_SPECS: tuple[CredentialSpec, ...] = (
    CredentialSpec("OPENROUTER_API_KEY", "OpenRouter", "API key", ("OPENROUTER_KEY",)),
    CredentialSpec("GEMINI_API_KEY", "Google Gemini", "API key", ("GOOGLE_API_KEY",)),
    CredentialSpec("OPENAI_API_KEY", "OpenAI / ChatGPT", "API key", ("CHATGPT_API_KEY",)),
    CredentialSpec("GROQ_API_KEY", "Groq", "API key", ("GROQ_KEY",)),
    CredentialSpec("MISTRAL_API_KEY", "Mistral", "API key", ("MISTRAL_KEY",)),
    CredentialSpec("CLOUDFLARE_API_TOKEN", "Cloudflare", "API token", ("CF_API_TOKEN",)),
    CredentialSpec("CLOUDFLARE_ACCOUNT_ID", "Cloudflare", "account ID", ("CF_ACCOUNT_ID",)),
    CredentialSpec("SILICONFLOW_API_KEY", "SiliconFlow", "API key", ("SILICON_FLOW_API_KEY",)),
    CredentialSpec("VENICE_API_KEY", "Venice", "API key"),
    CredentialSpec("POLLINATIONS_API_KEY", "Pollinations", "API key"),
    CredentialSpec("COHERE_API_KEY", "Cohere", "API key", ("CO_API_KEY",)),
    CredentialSpec("REPLICATE_API_TOKEN", "Replicate", "API token", ("REPLICATE_API_KEY",)),
    CredentialSpec("STABILITY_API_KEY", "Stability AI", "API key"),
    CredentialSpec(
        "NVIDIA_API_KEY",
        "NVIDIA Build/NIM",
        "API key",
        ("NVIDIA_NIM_API_KEY", "NGC_API_KEY"),
    ),
    CredentialSpec("ZAI_API_KEY", "Z.AI", "API key", ("ZHIPUAI_API_KEY", "GLM_API_KEY")),
    CredentialSpec("AION_API_KEY", "Aion Labs", "API key"),
    CredentialSpec("ZENMUX_API_KEY", "ZenMux", "API key"),
    CredentialSpec("ZENMUX_MANAGEMENT_API_KEY", "ZenMux", "management API key", optional=True),
    CredentialSpec("CEREBRAS_API_KEY", "Cerebras", "API key"),
    CredentialSpec("BLACKBOX_API_KEY", "BLACKBOX AI", "API key"),
    CredentialSpec("PUTER_AUTH_TOKEN", "Puter", "authorization token", optional=True),
)

_SPEC_BY_NAME = {spec.env_name: spec for spec in CREDENTIAL_SPECS}
_ALIAS_TO_CANONICAL = {
    alias: spec.env_name for spec in CREDENTIAL_SPECS for alias in spec.aliases
}
_PROVIDER_MATCHES: dict[str, tuple[str, ...]] = {
    "GEMINI_API_KEY": ("gemini", "google", "generativelanguage.googleapis.com"),
    "OPENROUTER_API_KEY": ("openrouter", "openrouter.ai"),
    "OPENAI_API_KEY": ("openai", "chatgpt", "api.openai.com"),
    "GROQ_API_KEY": ("groq", "api.groq.com"),
    "MISTRAL_API_KEY": ("mistral", "api.mistral.ai"),
    "CLOUDFLARE_API_TOKEN": ("cloudflare", "workers-ai", "api.cloudflare.com"),
    "SILICONFLOW_API_KEY": ("siliconflow", "silicon-flow", "api.siliconflow"),
    "VENICE_API_KEY": ("venice", "api.venice.ai"),
    "POLLINATIONS_API_KEY": ("pollinations", "pollinations.ai"),
    "COHERE_API_KEY": ("cohere", "api.cohere.ai"),
    "REPLICATE_API_TOKEN": ("replicate", "api.replicate.com"),
    "STABILITY_API_KEY": ("stability", "stability-ai", "api.stability.ai"),
    "NVIDIA_API_KEY": ("nvidia", "nim", "integrate.api.nvidia.com"),
    "ZAI_API_KEY": ("zai", "z.ai", "zhipu", "bigmodel"),
    "AION_API_KEY": ("aion", "aionlabs"),
    "ZENMUX_API_KEY": ("zenmux", "zenmux.ai"),
    "CEREBRAS_API_KEY": ("cerebras", "api.cerebras.ai"),
    "BLACKBOX_API_KEY": ("blackbox", "blackbox.ai"),
    "PUTER_AUTH_TOKEN": ("puter", "api.puter.com"),
}
_KEY_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")


def _nonempty(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        parsed = dotenv_values(path, interpolate=False)
    except (OSError, UnicodeError):
        return {}
    return {key: value for key, raw in parsed.items() if (value := _nonempty(raw))}


def _canonical_name(name: str) -> str | None:
    if name in _SPEC_BY_NAME:
        return name
    return _ALIAS_TO_CANONICAL.get(name)


def _match_provider(provider_id: str, provider_config: Mapping[str, object]) -> str | None:
    haystack = " ".join(
        [
            provider_id,
            str(provider_config.get("name", "")),
            str(provider_config.get("base_url", "")),
        ]
    ).lower()
    for env_name, needles in _PROVIDER_MATCHES.items():
        if any(needle in haystack for needle in needles):
            return env_name
    return None


def _codex_home() -> Path:
    return Path(os.getenv("CODEX_HOME", Path.home() / ".codex")).expanduser()


def _codex_env_files(cwd: Path | None = None) -> list[Path]:
    codex_home = _codex_home()
    current = (cwd or Path.cwd()).resolve()
    candidates = [
        codex_home / ".env",
        codex_home / "keys.env",
        codex_home / "secrets.env",
        Path.home() / ".config" / "codex" / ".env",
        current / ".env",
        current / ".env.local",
    ]
    seen: set[Path] = set()
    result: list[Path] = []
    for candidate in candidates:
        candidate = candidate.expanduser()
        if candidate not in seen:
            seen.add(candidate)
            result.append(candidate)
    return result


def _discover_from_mapping(
    mapping: Mapping[str, str], source: str, found: dict[str, DiscoveredCredential]
) -> None:
    for source_name, value in mapping.items():
        canonical = _canonical_name(source_name)
        if canonical and canonical not in found and (clean := _nonempty(value)):
            found[canonical] = DiscoveredCredential(canonical, clean, source)


def _discover_from_codex_config(found: dict[str, DiscoveredCredential]) -> None:
    config_path = _codex_home() / "config.toml"
    if not config_path.is_file():
        return
    try:
        with config_path.open("rb") as handle:
            config = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return

    providers = config.get("model_providers", {})
    if isinstance(providers, dict):
        for provider_id, raw_provider in providers.items():
            if not isinstance(raw_provider, dict):
                continue
            target = _match_provider(str(provider_id), raw_provider)
            env_key = raw_provider.get("env_key")
            if target and isinstance(env_key, str) and (value := _nonempty(os.getenv(env_key))):
                found.setdefault(
                    target,
                    DiscoveredCredential(
                        target,
                        value,
                        f"Codex config provider '{provider_id}' via environment variable {env_key}",
                    ),
                )

    servers = config.get("mcp_servers", {})
    if isinstance(servers, dict):
        for server_name, raw_server in servers.items():
            if not isinstance(raw_server, dict):
                continue
            env_map = raw_server.get("env", {})
            if isinstance(env_map, dict):
                _discover_from_mapping(
                    {str(key): str(value) for key, value in env_map.items()},
                    f"Codex MCP server '{server_name}' environment map",
                    found,
                )
            env_vars = raw_server.get("env_vars", [])
            if isinstance(env_vars, list):
                inherited = {
                    str(name): os.environ[str(name)]
                    for name in env_vars
                    if isinstance(name, str) and name in os.environ
                }
                _discover_from_mapping(
                    inherited,
                    f"Codex MCP server '{server_name}' inherited environment",
                    found,
                )


def discover_credentials(
    env_path: Path = DEFAULT_ENV_FILE,
    *,
    cwd: Path | None = None,
) -> dict[str, DiscoveredCredential]:
    """Find recognized credentials without recursively scanning the user's home directory."""
    found: dict[str, DiscoveredCredential] = {}

    _discover_from_mapping(_read_dotenv(env_path), f"existing Lwa file {env_path}", found)

    process_values: dict[str, str] = {}
    for spec in CREDENTIAL_SPECS:
        for name in (spec.env_name, *spec.aliases):
            if name in os.environ:
                process_values[name] = os.environ[name]
    _discover_from_mapping(process_values, "current Codex/process environment", found)

    _discover_from_codex_config(found)

    for path in _codex_env_files(cwd):
        if path == env_path:
            continue
        _discover_from_mapping(
            _read_dotenv(path),
            f"recognized Codex/project env file {path}",
            found,
        )

    return found


def _quote_env_value(value: str) -> str:
    if "\x00" in value or "\n" in value or "\r" in value:
        raise ValueError("Credential values must be a single line and cannot contain NUL bytes.")
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def write_env_securely(
    values: Mapping[str, str],
    env_path: Path = DEFAULT_ENV_FILE,
    *,
    remove_names: Iterable[str] = (),
) -> Path:
    """Atomically write recognized values while preserving unknown custom entries."""
    env_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        env_path.parent.chmod(stat.S_IRWXU)
    except OSError:
        pass
    try:
        env_path.parent.chmod(stat.S_IRWXU)
    except OSError:
        pass

    template = files("lwa_mcp").joinpath("defaults/env.example").read_text(encoding="utf-8")
    existing = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    known_names = {spec.env_name for spec in CREDENTIAL_SPECS} | set(remove_names)

    unknown_lines: list[str] = []
    for line in existing.splitlines():
        match = _KEY_LINE.match(line)
        if match and match.group(1) not in known_names:
            unknown_lines.append(line)

    normalized = {key: value for key, raw in values.items() if (value := _nonempty(raw))}
    rendered: list[str] = []
    for line in template.splitlines():
        match = _KEY_LINE.match(line)
        if not match:
            rendered.append(line)
            continue
        name = match.group(1)
        if name in normalized:
            rendered.append(f"{name}={_quote_env_value(normalized[name])}")
        else:
            rendered.append(f"{name}=")

    if unknown_lines:
        rendered.extend(["", "# Preserved custom entries", *unknown_lines])

    payload = "\n".join(rendered).rstrip() + "\n"
    temp_path = env_path.with_name(f".{env_path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, env_path)
        os.chmod(env_path, 0o600)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return env_path


def _mask_credential(value: str) -> str:
    """Return display-only metadata; never return a complete credential."""
    if len(value) <= 4:
        return "••••"
    return f"{'•' * 8}{value[-4:]}"


def managed_credentials(env_path: Path = DEFAULT_ENV_FILE) -> list[dict[str, object]]:
    """Describe recognized entries in Lwa's env file without exposing their values."""
    values = _read_dotenv(env_path)
    result: list[dict[str, object]] = []
    for spec in CREDENTIAL_SPECS:
        source_name = next(
            (name for name in (spec.env_name, *spec.aliases) if _nonempty(values.get(name))),
            None,
        )
        value = values.get(source_name) if source_name else None
        result.append(
            {
                "env_name": spec.env_name,
                "provider": spec.provider,
                "label": spec.label,
                "optional": spec.optional,
                "configured": bool(value),
                "source_name": source_name,
                "masked": _mask_credential(value) if value else None,
            }
        )
    return result


def update_managed_credential(
    env_name: str,
    value: str | None,
    env_path: Path = DEFAULT_ENV_FILE,
) -> dict[str, object]:
    """Add, replace, or remove one recognized credential in the protected env file."""
    spec = _SPEC_BY_NAME.get(env_name)
    if spec is None:
        raise ValueError(f"Unsupported credential name: {env_name}")
    if value is not None:
        value = value.strip()
        if not value:
            raise ValueError("Credential values cannot be empty.")
        _quote_env_value(value)

    existing = _read_dotenv(env_path)
    values: dict[str, str] = {}
    for candidate in CREDENTIAL_SPECS:
        current = next(
            (existing[name] for name in (candidate.env_name, *candidate.aliases) if _nonempty(existing.get(name))),
            None,
        )
        if current:
            values[candidate.env_name] = current
    if value is None:
        values.pop(spec.env_name, None)
        for name in (spec.env_name, *spec.aliases):
            os.environ.pop(name, None)
    else:
        values[spec.env_name] = value
        os.environ[spec.env_name] = value
        for name in spec.aliases:
            os.environ.pop(name, None)
    write_env_securely(values, env_path, remove_names=spec.aliases)
    return next(item for item in managed_credentials(env_path) if item["env_name"] == env_name)


def _ask_yes_no(
    prompt: str,
    *,
    default: bool,
    input_func: Callable[[str], str],
    output: TextIO = sys.stdout,
) -> bool:
    suffix = " [Y/n] " if default else " [y/N] "
    while True:
        answer = input_func(prompt + suffix).strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please enter y or n.", file=output)


def run_credential_wizard(
    env_path: Path = DEFAULT_ENV_FILE,
    *,
    first_run: bool = False,
    specs: Iterable[CredentialSpec] | None = None,
    input_func: Callable[[str], str] = input,
    output: TextIO = sys.stdout,
    stdin_is_tty: bool | None = None,
    retry_configured: bool = False,
) -> dict[str, object]:
    """Interactive visible-input wizard. It intentionally never uses getpass()."""
    env_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        env_path.parent.chmod(stat.S_IRWXU)
    except OSError:
        pass
    tty = sys.stdin.isatty() if stdin_is_tty is None else stdin_is_tty
    if not tty:
        print(
            "Credential wizard skipped because standard input is not interactive. "
            "Run `lwa-router keys` in a terminal.",
            file=output,
        )
        return {"status": "non_interactive", "env_path": str(env_path)}

    selected_specs = tuple(specs or CREDENTIAL_SPECS)

    marker = env_path.parent / ".credential-wizard-complete"
    if first_run and marker.exists():
        existing = _read_dotenv(env_path)
        missing = [
            spec.env_name
            for spec in selected_specs
            if not spec.optional and not _nonempty(existing.get(spec.env_name))
        ]
        if not missing:
            print("Credential wizard already completed. Re-run with: lwa-router keys", file=output)
            return {"status": "already_completed", "env_path": str(env_path)}
        print(
            "Credential wizard previously completed, but these required entries are missing: "
            + ", ".join(missing)
            + ". Continuing setup.",
            file=output,
        )

    print("\nLwa MCP credential wizard", file=output)
    print("=========================", file=output)
    print(
        "Credential input is intentionally VISIBLE. Pasted values will appear in the terminal "
        "and remain in its scrollback so you can verify them.",
        file=output,
    )
    print(
        "Do not run this wizard while screen sharing or while another person can "
        "view the terminal.",
        file=output,
    )
    if not _ask_yes_no(
        "Continue with visible credential entry?",
        default=True,
        input_func=input_func,
        output=output,
    ):
        return {"status": "cancelled", "env_path": str(env_path)}

    discovered = discover_credentials(env_path)
    values = _read_dotenv(env_path)
    applicable = {spec.env_name for spec in selected_specs}
    discovered = {name: item for name, item in discovered.items() if name in applicable}

    if discovered:
        print("\nCredentials found in Lwa/Codex sources:", file=output)
        for spec in selected_specs:
            item = discovered.get(spec.env_name)
            if item:
                print(f"  {item.env_name}={item.value}", file=output)
                print(f"    source: {item.source}", file=output)
        if _ask_yes_no(
            "Store these exact discovered values in Lwa's protected .env?",
            default=True,
            input_func=input_func,
            output=output,
        ):
            values.update({name: item.value for name, item in discovered.items()})
        else:
            discovered = {}

    configured: list[str] = []
    skipped: list[str] = []
    input_ended = False
    for spec in selected_specs:
        if _nonempty(values.get(spec.env_name)) and not retry_configured:
            configured.append(spec.env_name)
            continue
        if spec.warning:
            print(f"\n{spec.provider}: {spec.warning}", file=output)
        while True:
            prompt = (
                f"\nPaste {spec.provider} {spec.label} for {spec.env_name} "
                + ("(visible; Enter to keep current): " if retry_configured else "(visible; Enter to skip): ")
            )
            try:
                value = input_func(prompt)
            except EOFError:
                print("\nInput ended; saving credentials entered so far.", file=output)
                input_ended = True
                skipped.extend(
                    remaining.env_name
                    for remaining in selected_specs
                    if remaining.env_name not in configured
                )
                break
            value = value.strip()
            if not value:
                if retry_configured and _nonempty(values.get(spec.env_name)):
                    configured.append(spec.env_name)
                skipped.append(spec.env_name)
                break
            try:
                _quote_env_value(value)
            except ValueError as exc:
                print(str(exc), file=output)
                continue
            print(f"Confirm exact value: {spec.env_name}={value}", file=output)
            if _ask_yes_no(
                "Save this exact value?",
                default=True,
                input_func=input_func,
                output=output,
            ):
                values[spec.env_name] = value
                configured.append(spec.env_name)
                break
            print("Value not saved; paste it again or press Enter to skip.", file=output)
        if input_ended:
            break

    write_env_securely(values, env_path)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(datetime.now(UTC).isoformat() + "\n", encoding="utf-8")
    marker.chmod(stat.S_IRUSR | stat.S_IWUSR)

    final_values = _read_dotenv(env_path)
    configured_names = [
        spec.env_name
        for spec in selected_specs
        if _nonempty(final_values.get(spec.env_name))
    ]
    missing_names = [
        spec.env_name for spec in selected_specs if spec.env_name not in configured_names
    ]
    print(f"\nSaved protected environment file: {env_path}", file=output)
    print("Permissions: 0600", file=output)
    print(f"Configured entries: {len(configured_names)}", file=output)
    print(f"Skipped or missing entries: {len(missing_names)}", file=output)
    print("Re-run at any time with: lwa-router keys", file=output)
    return {
        "status": "completed",
        "env_path": str(env_path),
        "configured": configured_names,
        "missing": missing_names,
    }
