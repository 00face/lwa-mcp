"""Server-side limits for multi-agent exchange controls."""

from __future__ import annotations


class ControlError(ValueError):
    pass


DEFAULTS = {"analysis_depth": "medium", "response_depth": "medium", "task_turns": 1,
            "provider_count": 1, "consensus_rounds": 1}
MAXIMUMS = {"task_turns": 20, "provider_count": 8, "consensus_rounds": 8}
DEPTHS = {"low", "medium", "high", "short", "long"}


def effective_controls(values: dict[str, str | int] | None = None, *, parent: dict[str, str | int] | None = None) -> dict[str, str | int]:
    result = dict(DEFAULTS)
    for key, value in (values or {}).items():
        if key not in result:
            raise ControlError(f"unknown control: {key}")
        if key in MAXIMUMS:
            if not isinstance(value, int) or value < 1:
                raise ControlError(f"invalid control: {key}")
            if value > MAXIMUMS[key]:
                raise ControlError(f"control exceeds maximum: {key}")
            if parent and value > int(parent.get(key, MAXIMUMS[key])):
                raise ControlError(f"child control would widen parent: {key}")
        elif value not in DEPTHS:
            raise ControlError(f"invalid depth: {key}")
        result[key] = value
    return result
