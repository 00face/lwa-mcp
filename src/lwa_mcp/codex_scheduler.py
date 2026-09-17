"""Render-only systemd user scheduler adapter for Codex Rites."""

from __future__ import annotations

import re
from pathlib import Path

from .rites import RiteManifest


class SchedulerError(ValueError):
    pass


def render_systemd(rite: RiteManifest, workspace: str | Path) -> tuple[str, str]:
    if rite.trigger.kind != "cron" or not rite.trigger.cron:
        raise SchedulerError("systemd adapter requires a cron trigger")
    match = re.fullmatch(r"(\d+)\s+(\d+)\s+\*\s+\*\s+\*", rite.trigger.cron)
    if not match:
        raise SchedulerError("only five-field daily cron expressions are supported")
    minute, hour = match.groups()
    root = str(Path(workspace).expanduser().resolve())
    service = f"""[Unit]\nDescription=Lwa Rite {rite.name}\n\n[Service]\nType=oneshot\nWorkingDirectory={root}\nEnvironment=LWA_WORKSPACE_ROOT={root}\nExecStart=/usr/bin/env lwa-rite-preflight {rite.name}\nExecStart=/usr/bin/env codex exec --sandbox workspace-write {rite.agent.task}\nTimeoutStartSec=30m\n"""
    timer = f"""[Unit]\nDescription=Schedule Lwa Rite {rite.name}\n\n[Timer]\nOnCalendar=*-*-* {int(hour):02d}:{int(minute):02d}:00\nPersistent=true\nUnit={rite.name}.service\n\n[Install]\nWantedBy=timers.target\n"""
    return service, timer
