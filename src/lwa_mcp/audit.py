"""Final evidence-gated audit for near-zero live quota usage."""

from __future__ import annotations

from typing import Any

MANDATORY_GATES = (
    "telemetry",
    "quota",
    "benchmark",
    "handshake",
    "safety",
)


def audit_near_zero_proof(bundle: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    gates: dict[str, bool] = {}
    for name in MANDATORY_GATES:
        evidence = bundle.get(name)
        if name == "handshake":
            passed = isinstance(evidence, dict) and evidence.get("status") == "passed"
        else:
            passed = isinstance(evidence, dict) and evidence.get("valid") is True
        gates[name] = passed
        if not passed:
            blockers.append(f"{name}_gate_failed")

    ten_of_ten = all(gates.values())
    predictive_reuse = bundle.get("predictive_reuse") is True
    stale_safeguards = bundle.get("stale_result_safeguards") is True
    independent_reproduction = bundle.get("independent_reproduction") is True
    eleven_of_ten = ten_of_ten and predictive_reuse and stale_safeguards and independent_reproduction
    if not predictive_reuse:
        blockers.append("predictive_reuse_unproven")
    if not stale_safeguards:
        blockers.append("stale_result_safeguards_unproven")
    if not independent_reproduction:
        blockers.append("independent_reproduction_unproven")
    return {
        "ten_of_ten": ten_of_ten,
        "eleven_of_ten": eleven_of_ten,
        "gates": gates,
        "blockers": blockers,
        "denominator_proof": gates["quota"],
        "quality_proof": gates["benchmark"],
        "live_proof": ten_of_ten,
    }
