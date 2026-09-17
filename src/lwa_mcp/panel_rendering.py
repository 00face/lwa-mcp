"""Pure geometry helpers used by the curses panel renderer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PanelGeometry:
    rows: int
    columns: int
    left_width: int
    right_column: int
    right_width: int
    native_split: bool

    @classmethod
    def from_screen(cls, rows: int, columns: int, *, native_split: bool) -> PanelGeometry:
        left_width = columns - 1 if native_split else max(28, min(columns // 3, 48))
        right_column = left_width + 1
        return cls(rows, columns, left_width, right_column, max(1, columns - right_column), native_split)

    @property
    def feed_start(self) -> int:
        return 3

    @property
    def lwa_prompt_heading(self) -> int:
        return self.rows - 6

    @property
    def codex_prompt_heading(self) -> int:
        return self.rows - 9

    @property
    def feed_height(self) -> int:
        return max(1, self.codex_prompt_heading - 1 - self.feed_start)

    def clamp_scroll(self, value: int, item_count: int, viewport: int | None = None) -> int:
        height = self.feed_height if viewport is None else max(1, viewport)
        return max(0, min(max(0, item_count - height), value))


def cursor_row(heading: int, multiline_offset: int) -> int:
    """Keep cursor placement within the two-line prompt viewport."""
    return heading + (2 if multiline_offset else 1)
