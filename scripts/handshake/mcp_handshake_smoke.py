#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    started = time.monotonic()
    try:
        command = shlex.split(args.command)
        if not command:
            raise ValueError("empty command")
        subprocess.run(command, shell=False, cwd=args.root, timeout=args.timeout, check=False)
    except subprocess.TimeoutExpired:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error": "mcp_handshake_timeout",
                    "elapsed_ms": int((time.monotonic() - started) * 1000),
                    "provider_calls": 0,
                }
            ),
            file=sys.stderr,
        )
        return 1
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error": "mcp_handshake_command_invalid",
                    "detail": str(exc),
                    "elapsed_ms": int((time.monotonic() - started) * 1000),
                    "provider_calls": 0,
                }
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps({"status": "ready", "elapsed_ms": int((time.monotonic() - started) * 1000), "provider_calls": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
