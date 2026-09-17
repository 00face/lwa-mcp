"""Disposable PostToolUse host-contract harness."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HarnessResult:
    """Observable result of one synthetic host-to-hook invocation."""

    exit_code: int
    stdout: str
    stderr: str
    valid_json: bool
    output_replaced: bool
    additional_context: bool

    @property
    def model_original_visible(self) -> bool:
        return False

    def host_visible_output(self, mode: str) -> str | None:
        """Model the output visible to the host under a declared contract."""
        if mode == "metadata-only":
            return None
        if mode == "replacement-capable":
            if not self.valid_json or not self.output_replaced:
                return None
            payload = json.loads(self.stdout)
            return payload["output"]
        if mode == "feedback-replacement":
            if not self.valid_json:
                return None
            payload = json.loads(self.stdout)
            return payload.get("stopReason") if payload.get("continue") is False else None
        if mode == "feedback-block":
            if not self.valid_json:
                return None
            payload = json.loads(self.stdout)
            return payload.get("reason") if payload.get("decision") == "block" else None
        if mode == "native-replacement":
            return None
        raise ValueError("unknown host mode")

    def contract_flags(self, mode: str) -> dict[str, bool]:
        """Return explicit visibility and semantic flags for a host mode."""
        visible = self.host_visible_output(mode) is not None
        return {
            "model_original_visible": self.model_original_visible,
            "model_replacement_visible": visible,
            "replacement_complete": visible and mode != "native-replacement",
            "tool_semantics_preserved": mode in {"metadata-only", "feedback-replacement", "replacement-capable"},
            "native_replacement": mode == "native-replacement" and self.output_replaced,
        }

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _mutation_fields(value: object) -> tuple[bool, bool]:
    if not isinstance(value, dict):
        return False, False
    return "output" in value, "additional_context" in value


def run_hook(hook: Path, event: dict[str, Any], *, timeout: float = 5.0) -> HarnessResult:
    """Run one hook with a JSON event and classify its observable response."""
    if not hook.is_file():
        raise FileNotFoundError(f"hook does not exist: {hook}")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    try:
        completed = subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps(event), text=True, capture_output=True,
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return HarnessResult(124, exc.stdout or "", exc.stderr or "timeout", False, False, False)
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        payload = None
    replaced, context = _mutation_fields(payload)
    return HarnessResult(
        completed.returncode, completed.stdout, completed.stderr,
        payload is not None, replaced, context,
    )


def run_fixture(hook: Path, *, output: str, exit_code: int = 0, timeout: float = 5.0,
                max_feedback_tokens: int = 2200) -> HarnessResult:
    """Run a synthetic tool result through a hook."""
    event = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "fixture-test"},
        "tool_output": output,
        # Some host proposals call the model-visible field `output`; retaining
        # both names lets the harness distinguish adapter capability from the
        # installed host's observed metadata-only envelope.
        "output": output,
        "exit_code": exit_code,
        "max_feedback_tokens": max_feedback_tokens,
        "cwd": str(Path.cwd()),
    }
    return run_hook(hook, event, timeout=timeout)
