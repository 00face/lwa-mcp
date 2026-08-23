"""Validate two exported live benchmark runs without invoking a provider."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lwa_mcp.live_benchmark import validate_repeated_runs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--allow-offline-fixture", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.evidence.read_text(encoding="utf-8"))
    result = validate_repeated_runs(payload, require_live=not args.allow_offline_fixture)
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
