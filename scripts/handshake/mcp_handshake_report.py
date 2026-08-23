#!/usr/bin/env python3
"""Report cache age and manifest counts without starting an MCP server."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="~/.cache/lwa-mcp/mcp-capabilities.json")
    args = parser.parse_args()
    path = Path(args.cache).expanduser()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest = payload["manifest"]
        report = {
            "status": "ready",
            "cache": str(path),
            "cache_age_seconds": round(max(0, time.time() - float(payload["saved_at"])), 3),
            "cache_key": payload["cache_key"],
            "protocol_version": manifest["protocol_version"],
            "tools": len(manifest["tools"]),
            "resources": len(manifest["resources"]),
            "prompts": len(manifest["prompts"]),
            "discovery_elapsed_ms": manifest["elapsed_ms"],
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "unavailable", "error": str(exc)}, separators=(",", ":")), file=sys.stderr)
        return 1
    print(json.dumps(report, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
