"""Fail-closed quota denominator reconciliation for live proof runs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

REQUIRED_SNAPSHOT_FIELDS = {
    "provider",
    "account_scope",
    "available_tokens",
    "unit",
    "captured_at",
    "reset_at",
    "source",
    "authoritative",
}


def _parse_time(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{field}_missing_or_invalid")
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{field}_invalid")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field}_timezone_required")
        return None
    return parsed.astimezone(UTC)


def reconcile_quota(
    snapshot: dict[str, Any],
    control_plane_tokens: int,
    *,
    now: datetime | None = None,
    max_age_seconds: int = 3600,
) -> dict[str, Any]:
    """Validate a quota snapshot and calculate overhead; invalid input never passes."""
    errors: list[str] = []
    missing = sorted(REQUIRED_SNAPSHOT_FIELDS - snapshot.keys())
    errors.extend(f"missing:{field}" for field in missing)
    provider = snapshot.get("provider")
    account_scope = snapshot.get("account_scope")
    if not provider:
        errors.append("provider_scope_missing")
    if not account_scope:
        errors.append("account_scope_missing")
    if snapshot.get("unit") != "tokens":
        errors.append("quota_unit_must_be_tokens")
    if snapshot.get("authoritative") is not True:
        errors.append("quota_not_authoritative")
    if snapshot.get("source") in {None, "nominal", "estimated", "unknown"}:
        errors.append("quota_source_not_authoritative")
    available = snapshot.get("available_tokens")
    if not isinstance(available, int) or available <= 0:
        errors.append("available_tokens_must_be_positive_integer")
    if not isinstance(control_plane_tokens, int) or control_plane_tokens < 0:
        errors.append("control_plane_tokens_must_be_nonnegative_integer")
    captured_at = _parse_time(snapshot.get("captured_at"), "captured_at", errors)
    reset_at = _parse_time(snapshot.get("reset_at"), "reset_at", errors)
    current = (now or datetime.now(UTC)).astimezone(UTC)
    if captured_at and (current - captured_at).total_seconds() > max_age_seconds:
        errors.append("quota_snapshot_stale")
    if captured_at and captured_at > current:
        errors.append("quota_snapshot_from_future")
    if reset_at and reset_at <= current:
        errors.append("quota_reset_window_expired")
    if captured_at and reset_at and reset_at <= captured_at:
        errors.append("quota_reset_before_capture")
    valid = not errors
    percentage = round(control_plane_tokens / available * 100, 6) if valid else None
    return {
        "valid": valid,
        "provider": provider,
        "account_scope": account_scope,
        "control_plane_tokens": control_plane_tokens,
        "available_tokens": available,
        "overhead_percent": percentage,
        "under_0_1_percent": bool(valid and percentage < 0.1),
        "errors": errors,
        "denominator_definition": "control-plane tokens / authoritative available provider quota tokens",
    }
