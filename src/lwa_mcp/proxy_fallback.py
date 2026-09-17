"""Explicit recovery policy for schema-proxy failures."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from .proxy_forwarder import ForwardResult, forward_tool


@dataclass(frozen=True)
class FallbackDecision:
    mode: str
    reason: str
    retry_allowed: bool = False


def direct_fallback(reason: str, *, execution_started: bool = False) -> FallbackDecision:
    """Return a visible direct-mode recovery decision without hidden failover."""
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("fallback reason must be non-empty")
    if execution_started:
        return FallbackDecision("stop", reason, False)
    return FallbackDecision("direct", reason, False)


async def forward_or_recover(
    invoke: Callable[[str, dict], Awaitable[object]],
    tool: str,
    arguments: dict,
    *,
    allowed_tools: frozenset[str],
    execution_started: bool = False,
) -> ForwardResult | FallbackDecision:
    """Forward once, returning an explicit recovery decision on failure."""
    try:
        result = await forward_tool(invoke, tool, arguments, allowed_tools=allowed_tools)
    except (TypeError, ValueError, OSError) as exc:
        return direct_fallback(str(exc), execution_started=execution_started)
    if result.is_error:
        return direct_fallback(str(result.content), execution_started=execution_started)
    return result
