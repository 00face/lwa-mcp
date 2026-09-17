"""Safety and rollback fault-injection evidence for quota optimizations."""

from __future__ import annotations

from typing import Any

REQUIRED_SCENARIOS = {
    "provider_failure",
    "stale_cache",
    "missing_quota",
    "missing_usage",
    "duplicate_execution",
    "rollback",
}


def default_fault_evidence() -> dict[str, dict[str, Any]]:
    return {
        "provider_failure": {
            "blocked": True,
            "status": "repreflight_required",
            "provider_calls": 1,
            "followup_routes": 0,
        },
        "stale_cache": {"blocked": True, "cache_reuse": False, "provider_calls": 0},
        "missing_quota": {"blocked": True, "proof_valid": False, "provider_calls": 0},
        "missing_usage": {"blocked": True, "proof_valid": False, "provider_calls": 0},
        "duplicate_execution": {"blocked": True, "duplicate_provider_executions": 0, "provider_calls": 0},
        "rollback": {
            "blocked": True,
            "response_detail": "standard",
            "cache_reuse": False,
            "result_reuse": False,
            "provider_calls": 0,
        },
    }


def validate_fault_evidence(evidence: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    missing = sorted(REQUIRED_SCENARIOS - evidence.keys())
    errors.extend(f"missing_scenario:{name}" for name in missing)
    for name, result in evidence.items():
        if name not in REQUIRED_SCENARIOS:
            errors.append(f"unknown_scenario:{name}")
            continue
        if result.get("blocked") is not True:
            errors.append(f"{name}:not_blocked")
        if result.get("provider_calls", 0) < 0:
            errors.append(f"{name}:invalid_provider_calls")
    provider_failure = evidence.get("provider_failure", {})
    if provider_failure.get("status") != "repreflight_required":
        errors.append("provider_failure:missing_repreflight")
    if provider_failure.get("followup_routes") != 0:
        errors.append("provider_failure:rerouted_after_failure")
    stale_cache = evidence.get("stale_cache", {})
    if stale_cache.get("cache_reuse") is not False:
        errors.append("stale_cache:reuse_not_disabled")
    duplicate = evidence.get("duplicate_execution", {})
    if duplicate.get("duplicate_provider_executions") != 0:
        errors.append("duplicate_execution:duplicate_detected")
    rollback = evidence.get("rollback", {})
    if rollback.get("response_detail") != "standard" or rollback.get("cache_reuse") is not False or rollback.get("result_reuse") is not False:
        errors.append("rollback:unsafe_state")
    return {
        "valid": not errors,
        "scenarios": len(evidence),
        "required_scenarios": len(REQUIRED_SCENARIOS),
        "provider_calls": sum(item.get("provider_calls", 0) for item in evidence.values()),
        "errors": errors,
        "promotion_blocked": bool(errors),
    }
