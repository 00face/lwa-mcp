"""Verify that an explicit quota snapshot is authoritative for the locked Zai route."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from lwa_mcp.quota import reconcile_quota


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--account-scope", required=True)
    parser.add_argument("--control-plane-tokens", type=int, required=True)
    parser.add_argument("--now", required=True)
    parser.add_argument("--max-age-seconds", type=int, default=3600)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    errors = []
    if snapshot.get("provider") != "zai":
        errors.append("provider_must_be_zai")
    if snapshot.get("account_scope") != args.account_scope:
        errors.append("account_scope_mismatch")
    result = reconcile_quota(
        snapshot,
        args.control_plane_tokens,
        now=datetime.fromisoformat(args.now),
        max_age_seconds=args.max_age_seconds,
    )
    result["errors"] = errors + result["errors"]
    result["valid"] = not result["errors"]
    result["under_0_1_percent"] = result["valid"] and result["overhead_percent"] < 0.1
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
