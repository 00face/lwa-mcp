#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def inspect_cache(path: Path, providers: list[str], max_age_seconds: float) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        age = max(0.0, time.time() - float(payload["saved_at"]))
        cached = set(payload.get("providers") or [])
    except (OSError, ValueError, KeyError, TypeError):
        return {"status": "live_refresh_required", "reason": "cache_missing_or_invalid", "providers": providers, "network_calls": 0}
    if age <= max_age_seconds and set(providers) <= cached:
        return {"status": "cache_hit", "cache_age_seconds": age, "providers": providers, "network_calls": 0}
    return {"status": "live_refresh_required", "reason": "provider_scope_missing", "providers": providers, "network_calls": 0}
