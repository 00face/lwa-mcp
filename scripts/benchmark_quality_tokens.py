#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from lwa_mcp.benchmark import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quota-tokens", type=int)
    args = parser.parse_args()
    print(json.dumps(run_benchmark(quota_tokens=args.quota_tokens), indent=2))


if __name__ == "__main__":
    main()
