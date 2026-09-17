"""Render-only AGY sidecar and Skill adapter for portable Agent Rites."""

from __future__ import annotations

from pathlib import Path

from .rites import RiteManifest


class AgyAdapterError(ValueError):
    pass


def render_agy(rite: RiteManifest, workspace: str | Path) -> dict[str, object]:
    if rite.trigger.kind != "cron" or not rite.trigger.cron:
        raise AgyAdapterError("AGY schedule adapter requires a cron trigger")
    root = str(Path(workspace).expanduser().resolve())
    return {
        "sidecar": {"description": f"Lwa Rite {rite.name}", "builtin": "schedule",
                     "args": [rite.trigger.cron, "agentapi", "new-conversation", f"/{rite.agent.task}"],
                     "workingDirectory": root},
        "skill": f"---\nname: {rite.agent.task}\ndescription: Recurring Lwa Rite {rite.name}\n---\n\nRun the {rite.agent.task} task after Lwa preflight and HardGate verification.\n",
        "installed": False,
    }
