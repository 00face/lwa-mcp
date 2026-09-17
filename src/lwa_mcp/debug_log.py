"""Safe, local diagnostics for the native LWA terminal surface."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import load_config
from .terminal_protocol import detect_terminal_capabilities, redact_terminal_text


def collect_debug_snapshot(
    *,
    executable: str | None,
    session_active: bool,
    pipeline_busy: bool,
    scroll_offset: int,
    rows: int,
    columns: int,
) -> dict[str, Any]:
    """Collect operational facts without prompts, environment values, or secrets."""
    codex = executable or shutil.which("codex")
    version = "unavailable"
    if codex:
        try:
            result = subprocess.run(
                [codex, "--version"], capture_output=True, text=True, timeout=2, check=False
            )
            version = result.stdout.strip()[:120] or result.stderr.strip()[:120] or "unknown"
        except (OSError, subprocess.SubprocessError):
            version = "error"
    settings = load_config().settings
    dashboard_url = f"http://{settings.dashboard_host}:{settings.dashboard_port}"
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "application": "lwa-native-terminal",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": str(Path.cwd()),
        "terminal": {
            "rows": rows,
            "columns": columns,
            "term": os.getenv("TERM", ""),
            "capabilities": detect_terminal_capabilities().public_json(),
        },
        "codex": {"path": codex or "not-found", "version": version},
        "session": {
            "active": session_active,
            "pipeline_busy": pipeline_busy,
            "scroll_offset": scroll_offset,
        },
        "dashboard": {"url": dashboard_url},
        "privacy": {
            "prompts_recorded": False,
            "environment_values_recorded": False,
            "credentials_recorded": False,
        },
    }


def write_debug_log(snapshot: dict[str, Any]) -> Path:
    path = Path.home() / ".local" / "state" / "lwa-mcp" / "debug.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(snapshot, separators=(",", ":")) + "\n")
    path.chmod(0o600)
    return path


def write_startup_error(application: str, exc: BaseException) -> Path:
    """Persist a redacted startup failure for crashes before the TUI is usable."""
    path = Path.home() / ".local" / "state" / "lwa-mcp" / "startup.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    message = redact_terminal_text(str(exc)).replace("\x1b", "")
    trace = redact_terminal_text("".join(traceback.format_exception(exc))).replace("\x1b", "")
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "application": application,
        "cwd": str(Path.cwd()),
        "error_type": type(exc).__name__,
        "message": message[:1000],
        "traceback": trace[-8000:],
        "privacy": {
            "prompts_recorded": False,
            "environment_values_recorded": False,
            "credentials_recorded": False,
        },
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    path.chmod(0o600)
    return path


def write_startup_event(application: str, event: str) -> Path:
    """Record a minimal, secret-free launcher lifecycle event."""
    path = Path.home() / ".local" / "state" / "lwa-mcp" / "startup.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "application": application,
        "event": event,
        "cwd": str(Path.cwd()),
        "python": sys.version.split()[0],
        "privacy": {
            "prompts_recorded": False,
            "environment_values_recorded": False,
            "credentials_recorded": False,
        },
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    path.chmod(0o600)
    return path


def format_debug_snapshot(snapshot: dict[str, Any], path: Path) -> list[str]:
    terminal = snapshot["terminal"]
    session = snapshot["session"]
    codex = snapshot["codex"]
    return [
        "DEBUG SNAPSHOT (safe metadata only)",
        f"LWA cwd: {snapshot['cwd']}",
        f"Python/platform: {snapshot['python']} / {snapshot['platform']}",
        f"Terminal: {terminal['columns']}x{terminal['rows']} · TERM={terminal['term']}",
        f"Codex: {codex['version']} · {codex['path']}",
        f"Session active={session['active']} · pipeline_busy={session['pipeline_busy']} · scroll={session['scroll_offset']}",
        f"Dashboard: {snapshot['dashboard']['url']}",
        f"Debug log: {path} (mode 0600)",
    ]
