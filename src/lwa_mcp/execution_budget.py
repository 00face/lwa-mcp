"""Monotonic runtime counters derived from locked command controls."""

from __future__ import annotations

from dataclasses import dataclass, field

from .bounded_controls import effective_controls


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class ExecutionBudget:
    limits: dict[str, str | int]
    consumed: dict[str, int] = field(default_factory=dict)
    stop_reason: str | None = None

    def __post_init__(self) -> None:
        self.limits = effective_controls(self.limits)
        self.consumed = {key: 0 for key in self.limits if isinstance(self.limits[key], int)}

    @property
    def remaining(self) -> dict[str, int]:
        return {key: int(self.limits[key]) - self.consumed.get(key, 0)
                for key in self.consumed}

    def consume(self, control: str, amount: int = 1) -> None:
        if self.stop_reason is not None:
            raise BudgetExceeded(f"execution stopped: {self.stop_reason}")
        if control not in self.consumed or amount < 1:
            raise BudgetExceeded(f"unknown or invalid budget control: {control}")
        if self.consumed[control] + amount > int(self.limits[control]):
            raise BudgetExceeded(f"{control} limit reached")
        self.consumed[control] += amount

    def stop(self, reason: str) -> None:
        """Enter a terminal state; subsequent stop calls cannot rewrite evidence."""
        if not reason:
            raise ValueError("stop reason is required")
        if self.stop_reason is None:
            self.stop_reason = reason
