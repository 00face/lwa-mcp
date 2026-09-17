"""Configurable local MCP fixture server and lifecycle CLI."""

from __future__ import annotations

import argparse
import json
import os
import threading
from typing import Any

from mcp.server.fastmcp import FastMCP


def build_server(
    *,
    name: str,
    response: str,
    failure: str | None,
    mode: str,
    max_calls: int,
    idle_timeout: float,
) -> FastMCP:
    """Build a deterministic fixture server with explicit lifecycle settings."""
    server = FastMCP(name)
    calls = 0
    lock = threading.Lock()
    timer: threading.Timer | None = None

    def schedule_exit() -> None:
        if mode == "disposable" and calls >= max_calls:
            threading.Timer(0.2, lambda: os._exit(0)).start()

    if mode == "on-demand":
        timer = threading.Timer(idle_timeout, lambda: os._exit(0))
        timer.daemon = True
        timer.start()

    @server.tool()
    def fixture_echo(payload: str = "") -> str:
        """Return deterministic fixture data and call metadata."""
        nonlocal calls, timer
        with lock:
            calls += 1
            if timer is not None:
                timer.cancel()
            if failure:
                result: dict[str, Any] = {"error": failure, "call": calls}
            else:
                result = {"response": response, "payload": payload, "call": calls, "mode": mode}
            schedule_exit()
        return json.dumps(result, separators=(",", ":"))

    return server


def main() -> int:
    """Parse lifecycle configuration and serve the fixture over MCP stdio."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("disposable", "fixture", "always-on", "on-demand"), default="fixture")
    parser.add_argument("--name", default="Lwa MCP Fixture")
    parser.add_argument("--response", default="fixture-ok")
    parser.add_argument("--failure")
    parser.add_argument("--max-calls", type=int, default=1)
    parser.add_argument("--idle-timeout", type=float, default=30.0)
    args = parser.parse_args()
    if args.max_calls < 1 or args.idle_timeout <= 0:
        parser.error("--max-calls must be positive and --idle-timeout must be greater than zero")
    build_server(
        name=args.name, response=args.response, failure=args.failure, mode=args.mode,
        max_calls=args.max_calls, idle_timeout=args.idle_timeout,
    ).run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
