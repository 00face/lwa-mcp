"""Audit an exported near-zero live quota evidence bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lwa_mcp.audit import audit_near_zero_proof


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    result = audit_near_zero_proof(json.loads(args.bundle.read_text(encoding="utf-8")))
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["ten_of_ten"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
