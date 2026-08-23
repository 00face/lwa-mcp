"""Fail-closed guard for provider catalog refreshes; never performs network calls."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def inspect_cache(path: Path, providers: list[str], max_age_seconds: int) -> dict[str, object]:
    requested = sorted(set(providers))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        saved_at = float(payload["saved_at"])
        cached_providers = sorted(payload["providers"])
        if not set(requested) <= set(cached_providers):
            return {
                "status": "live_refresh_required",
                "reason": "provider_scope_missing",
                "providers": requested,
                "network_calls": 0,
            }
        age = max(0, time.time() - saved_at)
        if age > max_age_seconds:
            return {
                "status": "live_refresh_required",
                "reason": "catalog_cache_stale",
                "cache_age_seconds": round(age, 3),
                "providers": requested,
                "network_calls": 0,
            }
        return {
            "status": "cache_hit",
            "cache_age_seconds": round(age, 3),
            "providers": requested,
            "network_calls": 0,
        }
    except (OSError, TypeError, ValueError, KeyError):
        return {
            "status": "live_refresh_required",
            "reason": "cache_missing_or_invalid",
            "providers": requested,
            "network_calls": 0,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--provider", action="append", required=True)
    parser.add_argument("--max-age-seconds", type=int, default=3600)
    args = parser.parse_args()
    result = inspect_cache(args.cache, args.provider, args.max_age_seconds)
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["status"] == "cache_hit" else 2


if __name__ == "__main__":
    raise SystemExit(main())
