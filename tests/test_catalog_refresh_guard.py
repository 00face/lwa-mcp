import importlib.util
import json
import time
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "handshake" / "catalog_refresh_guard.py"
_SPEC = importlib.util.spec_from_file_location("catalog_refresh_guard", _SCRIPT)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
inspect_cache = _MODULE.inspect_cache


def test_catalog_guard_hits_fresh_scoped_cache(tmp_path):
    cache = tmp_path / "catalog.json"
    cache.write_text(json.dumps({"saved_at": time.time(), "providers": ["zai", "groq"]}), encoding="utf-8")

    result = inspect_cache(cache, ["zai"], 3600)

    assert result == {"status": "cache_hit", "cache_age_seconds": result["cache_age_seconds"], "providers": ["zai"], "network_calls": 0}


def test_catalog_guard_requires_explicit_scoped_refresh(tmp_path):
    cache = tmp_path / "catalog.json"
    cache.write_text(json.dumps({"saved_at": time.time() - 7200, "providers": ["groq"]}), encoding="utf-8")

    result = inspect_cache(cache, ["zai"], 3600)

    assert result["status"] == "live_refresh_required"
    assert result["reason"] == "provider_scope_missing"
    assert result["network_calls"] == 0


def test_catalog_guard_fails_closed_on_invalid_cache(tmp_path):
    result = inspect_cache(tmp_path / "missing.json", ["zai"], 3600)

    assert result == {
        "status": "live_refresh_required",
        "reason": "cache_missing_or_invalid",
        "providers": ["zai"],
        "network_calls": 0,
    }
