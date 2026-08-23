"""Verify a redacted telemetry export without deleting or hiding invalid rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lwa_mcp.db import UsageDB
from lwa_mcp.proof_telemetry import partition_proof_telemetry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--session-id")
    args = parser.parse_args()
    if bool(args.export) == bool(args.db):
        parser.error("provide exactly one of --export or --db")
    payload = (
        json.loads(args.export.read_text(encoding="utf-8"))
        if args.export
        else UsageDB(args.db).export_telemetry()
    )
    result = partition_proof_telemetry(payload, session_id=args.session_id)
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["proof_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
