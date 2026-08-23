"""Reconcile a redacted authoritative quota snapshot against control-plane tokens."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from lwa_mcp.quota import reconcile_quota


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--control-plane-tokens", type=int, required=True)
    parser.add_argument("--now", help="ISO-8601 time for deterministic validation")
    parser.add_argument("--max-age-seconds", type=int, default=3600)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    now = datetime.fromisoformat(args.now) if args.now else None
    if now and now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    result = reconcile_quota(
        snapshot,
        args.control_plane_tokens,
        now=now,
        max_age_seconds=args.max_age_seconds,
    )
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
