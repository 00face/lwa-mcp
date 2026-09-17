"""Opt-in stable-surface schema proxy contract."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .schema_router import RoutingDecision, classify_intent


@dataclass(frozen=True)
class ProxySurface:
    """The only tool schema a compatible proxy needs to advertise."""

    name: str = "route_capability"
    description: str = "Select and invoke relevant Lwa capabilities for a request."


class SchemaProxy:
    """Select candidates locally while leaving invocation to an injected host."""

    surface = ProxySurface()

    def __init__(self, invoke: Callable[[str, str], object]):
        self._invoke = invoke

    def plan(self, prompt: str) -> RoutingDecision:
        """Return a bounded routing plan without changing MCP discovery."""
        return classify_intent(prompt)

    def dispatch(self, prompt: str, payload: str) -> object:
        """Invoke the highest-confidence candidate or use the safe fallback."""
        decision = self.plan(prompt)
        return self._invoke(decision.tools[0], payload)
