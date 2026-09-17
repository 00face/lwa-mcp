"""Partition telemetry exports into eligible proof records and quarantined history."""

from __future__ import annotations

from typing import Any

from .telemetry import validate_telemetry_export


def partition_proof_telemetry(
    export: dict[str, Any], *, session_id: str | None = None
) -> dict[str, Any]:
    records = export.get("records") if isinstance(export.get("records"), list) else []
    eligible: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    reasons: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            quarantined.append({"record": record, "reasons": ["record_not_object"]})
            continue
        result = validate_telemetry_export({"schema_version": 1, "redacted": True, "records": [record]})
        record_reasons = list(result["errors"])
        if record.get("usage_status") != "reported":
            record_reasons.append("usage_status_not_reported")
        if session_id and record.get("session_id") != session_id:
            record_reasons.append("session_scope_mismatch")
        if record_reasons:
            quarantined.append({"record_id": record.get("id"), "reasons": record_reasons})
            reasons.extend(record_reasons)
        else:
            eligible.append(record)
    export_valid = validate_telemetry_export(export)["valid"]
    proof_valid = bool(records) and not quarantined and export_valid
    return {
        "proof_valid": proof_valid,
        "records_total": len(records),
        "eligible_records": len(eligible),
        "quarantined_records": len(quarantined),
        "eligible": eligible,
        "quarantined": quarantined,
        "reasons": sorted(set(reasons)),
        "historical_invalid_records_retained": True,
    }
