from __future__ import annotations

import os
import shutil
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values
from pydantic import BaseModel, Field

from .models import ConsentMode, ModelCandidate, ProviderConfig, parse_consent_mode

APP_NAME = "lwa-mcp"
STATE_DIR = Path(os.getenv("XDG_STATE_HOME", Path.home() / ".local/state")) / APP_NAME
CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME
DATA_DIR = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share")) / APP_NAME
DEFAULT_ENV_FILE = STATE_DIR / "lwa.env"
DEFAULT_CONFIG_FILE = CONFIG_DIR / "router.yaml"
DEFAULT_DB_FILE = STATE_DIR / "lwa.sqlite3"
DEFAULT_TOOL_LIBRARY_DIR = DATA_DIR / "tool-library"


class RouterSettings(BaseModel):
    consent_mode: ConsentMode = ConsentMode.PAID_ONLY
    prefer_free: bool = True
    allow_user_pays: bool = False
    allow_paid: bool = False
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8766
    catalog_refresh_minutes: int = 30
    confirmation_ttl_seconds: int = 600
    max_parallel_consensus: int = 3

    # Persistent reusable-tool doctrine.
    auto_detect_patterns: bool = True
    pattern_min_occurrences: int = 3
    pattern_similarity_threshold: float = 0.68
    auto_create_library_tools: bool = True
    auto_activate_prompt_tools: bool = True
    suggest_library_tools: bool = True
    max_library_suggestions: int = 5
    allow_reviewed_script_execution: bool = False

    # Optional post-response model-tier guidance. Disabled to preserve the
    # near-zero control-plane path unless an operator explicitly enables it.
    post_response_tier_guidance: bool = True
    post_response_tier_guidance_mode: str = "codex_request"

    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    models: list[ModelCandidate] = Field(default_factory=list)
    task_prompts: dict[str, str] = Field(default_factory=dict)


class LoadedConfig(BaseModel):
    settings: RouterSettings
    config_path: Path
    env_path: Path
    db_path: Path
    tool_library_path: Path

    model_config = {"arbitrary_types_allowed": True}


def ensure_dirs(
    *,
    state_dir: Path | None = STATE_DIR,
    config_dir: Path | None = CONFIG_DIR,
    data_dir: Path | None = DATA_DIR,
) -> None:
    """Create protected XDG directories, honoring explicit test/portable paths."""
    directories = tuple(directory for directory in (state_dir, config_dir, data_dir) if directory)
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    for private_dir in (state_dir, config_dir):
        if private_dir is None:
            continue
        try:
            private_dir.chmod(0o700)
        except OSError:
            pass


def install_default_config(source: Path | None = None, overwrite: bool = False) -> Path:
    ensure_dirs(state_dir=None, config_dir=DEFAULT_CONFIG_FILE.parent, data_dir=None)
    if DEFAULT_CONFIG_FILE.exists() and not overwrite:
        return DEFAULT_CONFIG_FILE
    if source is None:
        packaged = files("lwa_mcp").joinpath("defaults/router.example.yaml")
        DEFAULT_CONFIG_FILE.write_text(packaged.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        shutil.copyfile(source, DEFAULT_CONFIG_FILE)
    return DEFAULT_CONFIG_FILE


def load_config(config_path: Path | None = None, env_path: Path | None = None) -> LoadedConfig:
    ensure_dirs()
    config_path = config_path or Path(os.getenv("LWA_MCP_CONFIG", DEFAULT_CONFIG_FILE))
    env_path = env_path or Path(os.getenv("LWA_MCP_ENV_FILE", DEFAULT_ENV_FILE))
    if env_path.exists():
        # Keep credential values exact. python-dotenv interpolation would otherwise
        # expand token text containing ${...}. Existing process variables win.
        for key, value in dotenv_values(env_path, interpolate=False).items():
            if value is not None:
                os.environ.setdefault(key, value)
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            config_path.parent.chmod(0o700)
        except OSError:
            pass
        packaged = files("lwa_mcp").joinpath("defaults/router.example.yaml")
        config_path.write_text(packaged.read_text(encoding="utf-8"), encoding="utf-8")
    data: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if "consent_mode" in data and isinstance(data["consent_mode"], str):
        data["consent_mode"] = parse_consent_mode(data["consent_mode"])
    settings = RouterSettings.model_validate(data)
    db_path = Path(os.getenv("LWA_MCP_DB", DEFAULT_DB_FILE))
    tool_library_path = Path(os.getenv("LWA_MCP_TOOL_LIBRARY", DEFAULT_TOOL_LIBRARY_DIR))
    return LoadedConfig(
        settings=settings,
        config_path=config_path,
        env_path=env_path,
        db_path=db_path,
        tool_library_path=tool_library_path,
    )


def save_settings(config: LoadedConfig, settings: RouterSettings) -> None:
    payload = settings.model_dump(mode="json")
    config.config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        config.config_path.parent.chmod(0o700)
    except OSError:
        pass
    config.config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
