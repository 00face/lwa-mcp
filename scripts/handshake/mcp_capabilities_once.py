#!/usr/bin/env python3
"""Use a matching cached MCP capability manifest or perform one live discovery."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import anyio
from handshake_lib import base_identity, command_from_text, discover, load_cache, save_cache


async def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    command = command_from_text(root, args.command)
    cache_path = Path(args.cache).expanduser()
    identity = base_identity(command, root)
    if not args.refresh:
        cached = load_cache(cache_path, identity)
        if cached:
            print(json.dumps({"status": "cache_hit", "cache": str(cache_path), "manifest": cached["manifest"]}, separators=(",", ":")))
            return 0
    manifest = await discover(command, root, args.timeout)
    save_cache(cache_path, identity, manifest)
    print(json.dumps({"status": "cache_miss", "cache": str(cache_path), "manifest": manifest}, separators=(",", ":")))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--command")
    parser.add_argument("--cache", default="~/.cache/lwa-mcp/mcp-capabilities.json")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--refresh", action="store_true")
    try:
        return anyio.run(run, parser.parse_args())
    except TimeoutError:
        print(json.dumps({"status": "failed", "error": "mcp_handshake_timeout"}, separators=(",", ":")), file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "failed", "error": str(exc)}, separators=(",", ":")), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
