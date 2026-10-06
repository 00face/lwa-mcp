#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    started = time.monotonic()
    try:
        subprocess.run(args.command, shell=True, cwd=args.root, timeout=args.timeout, check=False)
    except subprocess.TimeoutExpired:
        print(json.dumps({"status": "failed", "error": "mcp_handshake_timeout", "elapsed_ms": int((time.monotonic() - started) * 1000), "provider_calls": 0}), file=__import__("sys").stderr)
        return 1
    print(json.dumps({"status": "ready", "elapsed_ms": int((time.monotonic() - started) * 1000), "provider_calls": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
