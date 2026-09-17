"""Fail-closed parser for Lwa's explicit CLI command modes."""

from __future__ import annotations

import shlex
from dataclasses import dataclass


class PrefixError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedCommand:
    mode: str
    command: str
    original: str
    controls: dict[str, str | int]


_MODES = {"!e": "direct", "!$": "skill", "!d": "delegated", "!c": "consensus"}
_DEFAULTS = {"analysis_depth": "medium", "response_depth": "medium", "task_turns": 1,
             "provider_count": 1, "consensus_rounds": 1}
_MAX = {"task_turns": 20, "provider_count": 8, "consensus_rounds": 8}
_ALIASES = {"analysis-depth": "analysis_depth", "response-depth": "response_depth",
            "depth": "analysis_depth", "turns": "task_turns", "providers": "provider_count",
            "rounds": "consensus_rounds"}


def parse_command(text: str) -> ParsedCommand:
    original = text
    tokens = shlex.split(text)
    if not tokens or tokens[0] not in _MODES:
        raise PrefixError("unknown prefix")
    prefix = tokens.pop(0)
    if any(token in _MODES or token.startswith("!") for token in tokens):
        raise PrefixError("nested command prefix")
    command_tokens: list[str] = []
    controls = dict(_DEFAULTS)
    for token in tokens:
        if token.startswith("--"):
            try:
                key, value = token[2:].split("=", 1)
                key = _ALIASES[key]
            except (ValueError, KeyError) as exc:
                raise PrefixError(f"unknown control: {token}") from exc
            if key in _MAX:
                try:
                    value = int(value)
                except ValueError as exc:
                    raise PrefixError(f"integer control required: {token}") from exc
                if value < 1 or value > _MAX[key]:
                    raise PrefixError(f"control exceeds maximum: {key}")
            elif key in {"analysis_depth", "response_depth"} and value not in {"low", "medium", "high", "short", "long"}:
                raise PrefixError(f"invalid depth: {value}")
            controls[key] = value
        else:
            command_tokens.append(token)
    if not command_tokens:
        raise PrefixError("command is required")
    return ParsedCommand(_MODES[prefix], " ".join(command_tokens), original, controls)
