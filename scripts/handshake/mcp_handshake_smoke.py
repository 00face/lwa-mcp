#!/usr/bin/env python3
"""Run a live MCP surface check without provider completion or quota probes."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import anyio
from handshake_lib import command_from_text, discover


async def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    manifest = await discover(command_from_text(root, args.command), root, args.timeout)
    print(json.dumps({"status": "passed", "manifest": manifest}, separators=(",", ":")))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--command")
    parser.add_argument("--timeout", type=float, default=8.0)
    started = time.monotonic()
    try:
        return anyio.run(run, parser.parse_args())
    except TimeoutError:
        print(json.dumps({
            "status": "failed",
            "error": "mcp_handshake_timeout",
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "provider_calls": 0,
        }, separators=(",", ":")), file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({
            "status": "failed",
            "error": str(exc),
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "provider_calls": 0,
        }, separators=(",", ":")), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
