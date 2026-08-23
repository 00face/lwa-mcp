"""Emit the offline WO-024D golden-set benchmark as compact JSON."""

from __future__ import annotations

import argparse
import json

from lwa_mcp.benchmark import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quota-tokens", type=int, default=None)
    args = parser.parse_args()
    print(json.dumps(run_benchmark(quota_tokens=args.quota_tokens), separators=(",", ":")))


if __name__ == "__main__":
    main()
