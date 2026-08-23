#!/usr/bin/env python3
"""Run an MCP stdio discovery handshake using the installed MCP client SDK."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REQUIRED_TOOLS = {"prepare_task", "approve_preflight", "run_prepared_task", "router_status"}
REQUIRED_RESOURCES = {"lwa://status", "lwa://catalog"}
REQUIRED_PROMPTS = {"preflight_guidance"}


async def run_handshake(command: list[str], root: Path, timeout: float) -> int:
    params = StdioServerParameters(command=command[0], args=command[1:], cwd=root)
    with anyio.fail_after(timeout):
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                initialized = await session.initialize()
                tools = {item.name for item in (await session.list_tools()).tools}
                resources = {str(item.uri) for item in (await session.list_resources()).resources}
                prompts = {item.name for item in (await session.list_prompts()).prompts}

    missing = {
        "tools": sorted(REQUIRED_TOOLS - tools),
        "resources": sorted(REQUIRED_RESOURCES - resources),
        "prompts": sorted(REQUIRED_PROMPTS - prompts),
    }
    if any(missing.values()):
        raise RuntimeError(f"MCP surface incomplete: {missing}")
    print(
        json.dumps(
            {
                "status": "passed",
                "protocol_version": initialized.protocolVersion,
                "tools": len(tools),
                "resources": len(resources),
                "prompts": len(prompts),
            },
            indent=2,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--command", help="MCP command; defaults to .venv/bin/lwa-mcp")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    command_text = args.command or os.environ.get("LWA_MCP_COMMAND")
    if command_text:
        command = shlex.split(command_text)
    else:
        installed = root / ".venv/bin/lwa-mcp"
        command = [str(installed if installed.exists() else "lwa-mcp")]
    try:
        return anyio.run(run_handshake, command, root, args.timeout)
    except FileNotFoundError:
        print(f"MCP command not found: {command[0]}", file=sys.stderr)
        return 2
    except TimeoutError:
        print(f"MCP handshake timed out after {args.timeout:g}s", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"MCP handshake failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
