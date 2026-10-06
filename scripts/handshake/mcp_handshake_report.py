#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = json.loads(args.cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(json.dumps({"status": "missing", "tools": 0}))
        return 1
    manifest = payload.get("manifest") or {}
    report = {"status": "ready", "tools": len(manifest.get("tools") or []), "resources": len(manifest.get("resources") or []), "prompts": len(manifest.get("prompts") or [])}
    print(json.dumps(report, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
