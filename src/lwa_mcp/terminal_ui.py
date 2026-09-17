"""Small dependency-free terminal presentation for routed work.

The MCP host owns the primary Codex conversation, so its selected model cannot
be discovered reliably from inside an MCP server.  Operators can pass it in
the environment or on the CLI; otherwise we say so explicitly instead of
presenting a guessed model as fact.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CodexIdentity:
    model: str | None = None
    reasoning: str | None = None

    @property
    def label(self) -> str:
        model = self.model or "unknown (host-owned)"
        return f"{model} · reasoning {self.reasoning}" if self.reasoning else model


def get_codex_identity(model: str | None = None, reasoning: str | None = None) -> CodexIdentity:
    """Read optional host-provided identity without claiming MCP can inspect Codex."""
    return CodexIdentity(
        model=model or os.getenv("LWA_CODEX_MODEL") or os.getenv("CODEX_MODEL"),
        reasoning=reasoning or os.getenv("LWA_CODEX_REASONING") or os.getenv("CODEX_REASONING_EFFORT"),
    )


def _route(preflight: dict[str, Any]) -> dict[str, Any]:
    routes = preflight.get("routes") or []
    if not routes:
        return {}
    route = routes[0]
    return route.get("decision", {}).get("candidate", {})


def _task_label(task: str) -> str:
    labels = {
        "conversation_compression": "CONVERSATION OPTIMIZATION",
        "token_optimization": "TOKEN OPTIMIZATION",
    }
    return labels.get(task, task.replace("_", " ").upper())


def _completion(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("result") or {}
    if result:
        return result
    synthesis = payload.get("synthesis") or {}
    return synthesis


def render_preflight(payload: dict[str, Any], identity: CodexIdentity) -> str:
    preflight = payload.get("preflight") or {}
    candidate = _route(preflight)
    route = f"{candidate.get('provider', '?')} / {candidate.get('model', '?')}"
    billing = str(candidate.get("billing_class", "unknown")).replace("_", " ")
    status = "READY" if preflight.get("working_may_begin") else "APPROVAL REQUIRED"
    effort = preflight.get("reasoning_effort") or "provider default"
    return "\n".join(
        [
            "╭─ LWA ROUTER ─────────────────────────────────────────────╮",
            f"│ CODEX  {identity.label}",
            f"│ LWA    {_task_label(str(preflight.get('task', 'task')))} · {status}",
            f"│ ROUTE  {route} · {billing}",
            f"│ EFFORT {effort}",
            (
                f"│ BUDGET {preflight.get('estimated_input_tokens', '?')} input · "
                f"{preflight.get('max_output_tokens', '?')} max output tokens"
            ),
            "╰───────────────────────────────────────────────────────────╯",
        ]
    )


def render_result(payload: dict[str, Any], identity: CodexIdentity) -> str:
    decision = payload.get("decision") or {}
    candidate = decision.get("candidate") or _route(payload.get("preflight") or {})
    result = _completion(payload)
    task = payload.get("preflight", {}).get("task", "task")
    route = f"{candidate.get('provider', result.get('provider', '?'))} / " \
        f"{candidate.get('model', result.get('model', '?'))}"
    billing = str(candidate.get("billing_class", "unknown")).replace("_", " ")
    text = result.get("text") or "(No displayable text was returned.)"
    return "\n".join(
        [
            "╭─ LWA RESPONSE ────────────────────────────────────────────╮",
            f"│ TASK   {_task_label(str(task))}",
            f"│ MODEL  {route}",
            f"│ BILLING {billing}",
            (
                f"│ TOKENS {result.get('input_tokens', '?')} input / "
                f"{result.get('output_tokens', '?')} output"
            ),
            "╰───────────────────────────────────────────────────────────╯",
            text,
            "────────────────────────────────────────────────────────────",
            f"[LWA] COMPLETE · {_task_label(str(task))}",
            f"[CODEX] ACTIVE · {identity.label}",
        ]
    )


def response_display(payload: dict[str, Any], identity: CodexIdentity | None = None) -> dict[str, Any]:
    """Return explicit, host-visible metadata without changing raw provider text."""
    identity = identity or get_codex_identity()
    preflight = payload.get("preflight") or {}
    candidate = _route(preflight)
    decision = payload.get("decision") or {}
    if not candidate:
        candidate = decision.get("candidate") or {}
    result = _completion(payload)
    return {
        "surface": "LWA",
        "phase": _task_label(str(preflight.get("task", "task"))),
        "provider": candidate.get("provider", result.get("provider")),
        "model": candidate.get("model", result.get("model")),
        "display_name": candidate.get("display_name"),
        "billing_class": candidate.get("billing_class", "unknown"),
        "reasoning_effort": preflight.get("reasoning_effort"),
        "input_tokens": result.get("input_tokens", 0),
        "output_tokens": result.get("output_tokens", 0),
        "returns_control_to": identity.label,
        "formatted": render_result(payload, identity),
    }


def _money(value: Any) -> str:
    return "not reported" if value is None else f"${float(value):.6f}"


def _optimization_line(task: str) -> str:
    if task == "token_optimization":
        return "✓ OPTIMIZE   token optimization requested · reduction measurement unavailable"
    if task == "conversation_compression":
        return "✓ COMPRESS   conversation compression requested · reduction measurement unavailable"
    return "· OPTIMIZE   not requested for this task"


def render_execution_telemetry(
    payload: dict[str, Any], identity: CodexIdentity | None = None
) -> str:
    """Render a compact but complete lifecycle trace for one execution."""
    identity = identity or get_codex_identity()
    preflight = payload.get("preflight") or {}
    decision = payload.get("decision") or {}
    candidate = decision.get("candidate") or _route(preflight)
    result = _completion(payload)
    display = payload.get("display") or {}
    task = str(preflight.get("task", "task"))
    route = f"{candidate.get('provider', result.get('provider', '?'))} / " \
        f"{candidate.get('model', result.get('model', '?'))}"
    billing = str(candidate.get("billing_class", "unknown")).replace("_", " ")
    quota = result.get("rate_limits") or {}
    quota_line = " · ".join(
        f"{key}={value}" for key, value in list(quota.items())[:3]
    ) or "no provider quota headers"
    credential = result.get("credential_env") or "default credential slot"
    subscription = display.get("subscription_plan") or "subscription not declared"
    actual_cost = result.get("cost_usd")
    estimated_cost = decision.get("estimated_max_cost_usd")
    optimization = _optimization_line(task)
    effort = preflight.get("reasoning_effort") or "provider default"
    return "\n".join(
        [
            "╭─ LWA TELEMETRY ────────────────────────────────────────────╮",
            f"│ TASK       {_task_label(task)}",
            f"│ ROUTE      {route}",
            f"│ EFFORT     {effort}",
            f"│ BILLING    {billing} · {subscription}",
            f"│ CREDENTIAL {credential} (name only; secret hidden)",
            "├─ LIFECYCLE ────────────────────────────────────────────────┤",
            "│ ✓ PREFLIGHT  prompt, budget, consent, and route locked",
            "│ ✓ ROUTE      provider/model selected before execution",
            "│ ✓ EXECUTE    locked provider call completed",
            f"│ {optimization}",
            "│ ✓ COMPLETE   result recorded in the local usage ledger",
            "│ → HANDOFF    control returns to Codex",
            "├─ USAGE & SPEND ─────────────────────────────────────────────┤",
            (
                f"│ TOKENS      {result.get('input_tokens', '?')} input + "
                f"{result.get('output_tokens', '?')} output"
            ),
            f"│ SPEND       actual {_money(actual_cost)} · estimated ceiling {_money(estimated_cost)}",
            f"│ LATENCY     {result.get('latency_ms', '?')} ms",
            f"│ QUOTA       {quota_line}",
            "╰───────────────────────────────────────────────────────────╯",
        ]
    )


def render_ledger_telemetry(status: dict[str, Any], identity: CodexIdentity | None = None) -> str:
    """Render recent persisted activity without exposing prompts or secrets."""
    identity = identity or get_codex_identity()
    usage = status.get("usage") or {}
    today = usage.get("today") or {}
    recent = usage.get("recent") or []
    lines = [
        "╭─ LWA TELEMETRY LEDGER ─────────────────────────────────────╮",
        f"│ CODEX      {identity.label}",
        (
            f"│ TODAY      {today.get('requests', 0)} requests · "
            f"{today.get('input_tokens', 0)} in / {today.get('output_tokens', 0)} out"
        ),
        f"│ SPEND      {_money(today.get('cost'))}",
        "├─ RECENT EXECUTIONS ────────────────────────────────────────┤",
    ]
    if not recent:
        lines.append("│ (no completed executions recorded)")
    else:
        for item in recent[:8]:
            route = f"{item.get('provider', '?')} / {item.get('model', '?')}"
            tokens = int(item.get("input_tokens", 0)) + int(item.get("output_tokens", 0))
            lines.append(
                f"│ {item.get('task', 'task'):24} {route:38} "
                f"{tokens:>6} tok · {_money(item.get('cost_usd'))}"
            )
    lines.append("╰───────────────────────────────────────────────────────────╯")
    return "\n".join(lines)
