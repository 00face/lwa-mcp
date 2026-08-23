"""Validate fail-closed safety and rollback evidence without provider calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lwa_mcp.safety import default_fault_evidence, validate_fault_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, nargs="?")
    args = parser.parse_args()
    evidence = default_fault_evidence() if args.evidence is None else json.loads(args.evidence.read_text(encoding="utf-8"))
    result = validate_fault_evidence(evidence)
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
