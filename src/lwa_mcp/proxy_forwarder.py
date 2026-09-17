"""Validated, bounded forwarding seam for the opt-in MCP schema proxy."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ForwardResult:
    tool: str
    content: object
    is_error: bool = False
    call_id: str | None = None


async def forward_tool(
    invoke: Callable[[str, dict], Awaitable[object]],
    tool: str,
    arguments: dict,
    *,
    allowed_tools: frozenset[str],
    timeout: float = 10.0,
    call_id: str | None = None,
) -> ForwardResult:
    """Forward one validated call through an upstream session boundary."""
    if tool not in allowed_tools:
        raise ValueError(f"tool is not allowed by proxy: {tool}")
    if not isinstance(arguments, dict):
        raise TypeError("arguments must be an object")
    if not 0.1 <= timeout <= 60:
        raise ValueError("timeout must be between 0.1 and 60 seconds")
    try:
        response = await asyncio.wait_for(invoke(tool, arguments), timeout)
    except TimeoutError:
        return ForwardResult(tool, {"error": "upstream timeout"}, True, call_id)
    is_error = bool(getattr(response, "isError", False) or getattr(response, "is_error", False))
    content = getattr(response, "content", response)
    response_call_id = getattr(response, "call_id", None) or getattr(response, "callId", None)
    return ForwardResult(tool, content, is_error, response_call_id or call_id)
