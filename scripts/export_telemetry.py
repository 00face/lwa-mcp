"""Export and validate redacted Lwa request telemetry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lwa_mcp.config import load_config
from lwa_mcp.db import UsageDB
from lwa_mcp.telemetry import validate_telemetry_export


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", help="SQLite path; defaults to the configured Lwa database")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    path = args.db or str(load_config().db_path)
    export = UsageDB(Path(path)).export_telemetry(args.limit)
    validation = validate_telemetry_export(export)
    print(json.dumps({"validation": validation, "export": export}, separators=(",", ":")))
    return 0 if validation["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
