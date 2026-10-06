#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--account-scope", required=True)
    parser.add_argument("--control-plane-tokens", type=int, required=True)
    parser.add_argument("--now")
    args = parser.parse_args()
    payload = json.loads(args.snapshot.read_text(encoding="utf-8"))
    if payload.get("provider") != "zai":
        print("provider_must_be_zai")
        return 2
    if payload.get("account_scope") != args.account_scope:
        print("account_scope_mismatch")
        return 2
    if int(payload.get("available_tokens", 0)) < args.control_plane_tokens:
        print("insufficient_tokens")
        return 2
    print(json.dumps({"status": "ok", "provider": "zai"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
