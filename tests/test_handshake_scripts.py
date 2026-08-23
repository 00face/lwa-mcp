from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts" / "handshake"))

from handshake_lib import base_identity, load_cache, manifest_is_complete, save_cache

COMPLETE_MANIFEST = {
    "protocol_version": "2025-03-26",
    "tools": ["approve_preflight", "prepare_task", "router_status", "run_prepared_task"],
    "resources": ["lwa://catalog", "lwa://status"],
    "prompts": ["preflight_guidance"],
    "elapsed_ms": 12,
}


def test_handshake_cache_hits_only_for_matching_identity(tmp_path):
    cache = tmp_path / "capabilities.json"
    identity = base_identity([str(tmp_path / "mcp")], tmp_path)
    save_cache(cache, identity, COMPLETE_MANIFEST)

    payload = load_cache(cache, identity)
    assert payload is not None
    assert payload["cache_key"]
    assert load_cache(cache, {**identity, "config_fingerprint": "changed"}) is None


def test_handshake_cache_rejects_incomplete_or_malformed_surface(tmp_path):
    cache = tmp_path / "capabilities.json"
    identity = base_identity(["mcp"], tmp_path)
    incomplete = {**COMPLETE_MANIFEST, "tools": ["prepare_task"]}
    save_cache(cache, identity, incomplete)
    assert not manifest_is_complete(incomplete)
    assert load_cache(cache, identity) is None

    cache.write_text("not-json", encoding="utf-8")
    assert load_cache(cache, identity) is None


def test_handshake_report_is_compact_and_provider_free(tmp_path):
    cache = tmp_path / "capabilities.json"
    identity = base_identity(["mcp"], tmp_path)
    save_cache(cache, identity, COMPLETE_MANIFEST)
    report_script = Path(__file__).parents[1] / "scripts" / "handshake" / "mcp_handshake_report.py"
    result = subprocess.run(
        [sys.executable, str(report_script), "--cache", str(cache)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["tools"] == 4


def test_handshake_smoke_timeout_reports_bounded_failure_metadata(tmp_path):
    smoke_script = Path(__file__).parents[1] / "scripts" / "handshake" / "mcp_handshake_smoke.py"
    result = subprocess.run(
        [sys.executable, str(smoke_script), "--root", str(tmp_path), "--command", "sh -c 'sleep 2'", "--timeout", "0.01"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    payload = json.loads(result.stderr)
    assert payload["status"] == "failed"
    assert payload["error"] == "mcp_handshake_timeout"
    assert payload["elapsed_ms"] >= 0
    assert payload["provider_calls"] == 0
