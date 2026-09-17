"""Validation for redacted telemetry evidence exports."""

from __future__ import annotations

from typing import Any

REQUIRED_RECORD_FIELDS = {
    "id",
    "created_at",
    "task",
    "provider",
    "model",
    "billing_class",
    "input_tokens",
    "output_tokens",
    "latency_ms",
    "status",
    "prompt_hash",
    "session_id",
    "call_id",
    "parent_call_id",
    "tool_name",
    "phase",
    "cache_hit",
    "redundant_call",
    "usage_status",
}
FORBIDDEN_RECORD_FIELDS = {"prompt", "text", "raw_usage", "metadata_json", "api_key", "token"}


def validate_telemetry_export(payload: dict[str, Any]) -> dict[str, Any]:
    """Return proof status; incomplete records are invalid, never silently accepted."""
    records = payload.get("records")
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("unsupported_schema_version")
    if payload.get("redacted") is not True:
        errors.append("export_not_marked_redacted")
    if not isinstance(records, list):
        errors.append("records_not_a_list")
        records = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record_{index}_not_an_object")
            continue
        missing = sorted(REQUIRED_RECORD_FIELDS - record.keys())
        forbidden = sorted(FORBIDDEN_RECORD_FIELDS & record.keys())
        if missing:
            errors.append(f"record_{index}_missing:{','.join(missing)}")
        if forbidden:
            errors.append(f"record_{index}_contains_sensitive:{','.join(forbidden)}")
        if record.get("usage_status") not in {"reported", "not_reported"}:
            errors.append(f"record_{index}_invalid_usage_status")
        for field in ("input_tokens", "output_tokens", "latency_ms"):
            if not isinstance(record.get(field), int) or record[field] < 0:
                errors.append(f"record_{index}_invalid_{field}")
        for field in ("session_id", "call_id", "parent_call_id", "tool_name", "phase"):
            if not record.get(field):
                errors.append(f"record_{index}_missing_attribution:{field}")
    return {
        "valid": not errors,
        "records": len(records),
        "reported_records": sum(item.get("usage_status") == "reported" for item in records if isinstance(item, dict)),
        "unreported_records": sum(item.get("usage_status") == "not_reported" for item in records if isinstance(item, dict)),
        "errors": errors,
    }
