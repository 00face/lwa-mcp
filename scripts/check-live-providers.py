#!/usr/bin/env python3
"""Perform explicit live catalog/quota probes; never submits completions."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys


async def run(include_quota: bool) -> int:
    from lwa_mcp.config import load_config
    from lwa_mcp.service import RouterService

    service = RouterService(load_config())
    catalog = await service.catalog.refresh(force=True)
    payload = {
        "status": "passed",
        "completion_requests_made": 0,
        "catalog": catalog,
        "providers": service.providers_json(),
    }
    if include_quota:
        payload["quotas"] = await service.refresh_provider_quotas()
    print(json.dumps(payload, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quota", action="store_true", help="Also call configured official quota/balance probes"
    )
    args = parser.parse_args()
    if os.environ.get("LWA_LIVE_PROVIDER_CHECK") != "1":
        print("Refusing live checks. Set LWA_LIVE_PROVIDER_CHECK=1 explicitly.", file=sys.stderr)
        return 2
    return asyncio.run(run(args.quota))


if __name__ == "__main__":
    raise SystemExit(main())
