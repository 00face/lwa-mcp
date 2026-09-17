"""Pure Codex and AGY pre-tool adapters for the shared constraint kernel."""

from __future__ import annotations

from typing import Any

from .constraints import ConstraintKernel


def _evaluate(payload: dict[str, Any], kernel: ConstraintKernel) -> tuple[bool, str]:
    if "command" in payload:
        result = kernel.check_command(payload["command"] if isinstance(payload["command"], list) else [str(payload["command"])])
    elif "path" in payload:
        result = kernel.check_path(str(payload["path"]))
    else:
        return False, "constraint kernel requires command or path input"
    return result.allowed, result.reason


def codex_pretool(payload: dict[str, Any], kernel: ConstraintKernel) -> dict[str, Any]:
    """Return a Codex hook response without executing or rewriting the tool."""
    allowed, reason = _evaluate(payload, kernel)
    output: dict[str, Any] = {"hookEventName": "PreToolUse", "permissionDecision": "allow" if allowed else "deny"}
    if not allowed:
        output["permissionDecisionReason"] = reason
    return {"hookSpecificOutput": output}


def agy_pretool(payload: dict[str, Any], kernel: ConstraintKernel) -> dict[str, Any]:
    """Return AGY's allow/deny decision for a proposed tool call."""
    allowed, reason = _evaluate(payload, kernel)
    return {"decision": "allow"} if allowed else {"decision": "deny", "reason": reason}
