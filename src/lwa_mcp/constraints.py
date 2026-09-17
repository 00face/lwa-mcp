"""Deterministic, fail-closed hard-constraint policy kernel."""

from __future__ import annotations

import fnmatch
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConstraintPolicyError(ValueError):
    """Raised when a constraint policy is malformed or unsupported."""


@dataclass(frozen=True)
class ConstraintResult:
    allowed: bool
    reason: str = ""


class ConstraintKernel:
    def __init__(self, policy: dict[str, Any]) -> None:
        if policy.get("version") != 1 or not isinstance(policy.get("hard"), dict):
            raise ConstraintPolicyError("policy version 1 and hard constraints are required")
        hard = policy["hard"]
        filesystem = hard.get("filesystem", {})
        commands = hard.get("commands", {})
        self._deny_paths = tuple(filesystem.get("deny_write", ()))
        self._deny_commands = tuple(commands.get("deny", ()))
        if not all(isinstance(value, str) for value in (*self._deny_paths, *self._deny_commands)):
            raise ConstraintPolicyError("constraint patterns must be strings")
        objectives = policy.get("objective", {}).get("minimize", ())
        self.objectives = tuple(objectives)

    @classmethod
    def from_file(cls, path: str | Path) -> "ConstraintKernel":
        try:
            policy = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise ConstraintPolicyError(str(exc)) from exc
        if not isinstance(policy, dict):
            raise ConstraintPolicyError("policy must be a mapping")
        return cls(policy)

    def check_path(self, path: str) -> ConstraintResult:
        normalized = path.replace("\\", "/").lstrip("./")
        for pattern in self._deny_paths:
            if fnmatch.fnmatchcase(normalized, pattern.lstrip("./")):
                return ConstraintResult(False, f"write denied by filesystem policy: {pattern}")
        return ConstraintResult(True)

    def check_command(self, command: list[str]) -> ConstraintResult:
        rendered = shlex.join(command)
        for pattern in self._deny_commands:
            if rendered == pattern or rendered.startswith(pattern + " "):
                return ConstraintResult(False, f"command denied by policy: {pattern}")
        return ConstraintResult(True)
