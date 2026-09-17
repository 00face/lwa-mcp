"""Minimal opt-in MCP schema proxy server."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from .schema_proxy import SchemaProxy


mcp = FastMCP("Lwa MCP Schema Proxy")
_proxy = SchemaProxy(lambda tool, payload: {"tool": tool, "payload": payload})


@mcp.tool()
def route_capability(prompt: str, payload: str = "") -> str:
    """Return a bounded capability plan; does not invoke an upstream tool."""
    decision = _proxy.plan(prompt)
    return json.dumps({
        "mode": "plan_only", "tools": decision.tools, "scores": decision.scores,
        "confidence": decision.confidence, "fallback": decision.fallback,
        "payload_received": bool(payload),
    }, separators=(",", ":"))


def main() -> None:
    """Run the proxy over MCP stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
