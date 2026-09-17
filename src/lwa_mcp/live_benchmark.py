"""Validation harness for repeated live golden-set benchmark evidence."""

from __future__ import annotations

from typing import Any

from .benchmark import GOLDEN_CASES, run_benchmark


def expected_fixture_manifest() -> list[dict[str, Any]]:
    measurements = run_benchmark()["runs"][0]["measurements"]
    return [
        {
            key: item[key]
            for key in ("name", "fixture_seed", "prompt_hash", "required_fields", "required_literals")
        }
        for item in measurements
        if item["detail"] == "compact"
    ]


def validate_repeated_runs(payload: dict[str, Any], *, require_live: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    runs = payload.get("runs")
    if not isinstance(runs, list) or len(runs) != 2:
        errors.append("exactly_two_runs_required")
        runs = []
    expected = expected_fixture_manifest()
    for index, run in enumerate(runs):
        if not isinstance(run, dict):
            errors.append(f"run_{index}_not_an_object")
            continue
        if run.get("fixture_manifest") != expected:
            errors.append(f"run_{index}_fixture_manifest_mismatch")
        if run.get("quality_delta_percentage_points", 99) > 1:
            errors.append(f"run_{index}_quality_regression")
        if run.get("telemetry_valid") is not True:
            errors.append(f"run_{index}_telemetry_invalid")
        if run.get("quota_valid") is not True:
            errors.append(f"run_{index}_quota_invalid")
        if run.get("duplicate_provider_executions", 1) != 0:
            errors.append(f"run_{index}_duplicate_provider_execution")
        if run.get("billing_classes", []) and not set(run["billing_classes"]) <= {"free", "free_quota"}:
            errors.append(f"run_{index}_unapproved_billing_class")
        if require_live and run.get("provider_executions", 0) < 1:
            errors.append(f"run_{index}_not_live")
        records = run.get("telemetry_records", [])
        if not records:
            errors.append(f"run_{index}_missing_telemetry_records")
        for record_index, record in enumerate(records):
            if record.get("usage_status") != "reported":
                errors.append(f"run_{index}_record_{record_index}_usage_not_reported")
            if not all(record.get(field) for field in ("session_id", "call_id", "parent_call_id", "tool_name", "phase")):
                errors.append(f"run_{index}_record_{record_index}_incomplete_attribution")
        metrics = run.get("metrics", {})
        if not isinstance(metrics, dict) or not {
            "input_tokens", "output_tokens", "tool_calls", "retries", "cache_hits", "p50_latency_ms", "p95_latency_ms"
        } <= metrics.keys():
            errors.append(f"run_{index}_metrics_incomplete")
    if (
        len(runs) == 2
        and runs[0].get("fixture_manifest") == runs[1].get("fixture_manifest")
        and runs[0].get("fixture_manifest") != expected
    ):
        errors.append("fixture_manifest_not_reproducible")
    return {
        "valid": not errors,
        "mode": "live_required" if require_live else "offline_fixture",
        "runs": len(runs),
        "cases": len(GOLDEN_CASES),
        "errors": errors,
        "promotion_blocked": bool(errors),
    }
