"""Small multiline line editor for the native LWA terminal frame."""

from __future__ import annotations


class PromptEditor:
    """Cursor-aware, dependency-free multiline prompt buffer."""

    def __init__(self) -> None:
        self.text = ""
        self.cursor = 0
        self.selection_anchor: int | None = None
        self._preferred_column: int | None = None

    @property
    def selection(self) -> tuple[int, int] | None:
        if self.selection_anchor is None or self.selection_anchor == self.cursor:
            return None
        return tuple(sorted((self.selection_anchor, self.cursor)))

    def selected_text(self) -> str:
        selected = self.selection
        return "" if selected is None else self.text[selected[0] : selected[1]]

    def _clear_selection(self) -> None:
        self.selection_anchor = None

    def insert(self, value: str) -> None:
        selected = self.selection
        if selected is not None:
            self.text = self.text[: selected[0]] + value + self.text[selected[1] :]
            self.cursor = selected[0] + len(value)
        else:
            self.text = self.text[: self.cursor] + value + self.text[self.cursor :]
            self.cursor += len(value)
        self._clear_selection()
        self._preferred_column = None

    def newline(self) -> None:
        self.insert("\n")

    def backspace(self) -> None:
        if self.selection is not None:
            self.insert("")
            return
        if self.cursor:
            self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
            self.cursor -= 1
        self._preferred_column = None

    def delete(self) -> None:
        if self.selection is not None:
            self.insert("")
            return
        if self.cursor < len(self.text):
            self.text = self.text[: self.cursor] + self.text[self.cursor + 1 :]
        self._preferred_column = None

    def left(self) -> None:
        self._clear_selection()
        self.cursor = max(0, self.cursor - 1)
        self._preferred_column = None

    def right(self) -> None:
        self._clear_selection()
        self.cursor = min(len(self.text), self.cursor + 1)
        self._preferred_column = None

    def _line_bounds(self) -> tuple[int, int]:
        start = self.text.rfind("\n", 0, self.cursor) + 1
        end = self.text.find("\n", self.cursor)
        return start, len(self.text) if end < 0 else end

    def home(self) -> None:
        self._clear_selection()
        self.cursor = self._line_bounds()[0]
        self._preferred_column = None

    def end(self) -> None:
        self._clear_selection()
        self.cursor = self._line_bounds()[1]
        self._preferred_column = None

    def _line_number_and_column(self) -> tuple[int, int]:
        before = self.text[: self.cursor]
        return before.count("\n"), len(before.rsplit("\n", 1)[-1])

    def _line_start(self, line_number: int) -> int:
        position = 0
        for _ in range(line_number):
            position = self.text.find("\n", position) + 1
            if position == 0:
                return len(self.text)
        return position

    def _line_end(self, start: int) -> int:
        end = self.text.find("\n", start)
        return len(self.text) if end < 0 else end

    def up(self) -> None:
        self._clear_selection()
        line, column = self._line_number_and_column()
        self._preferred_column = column if self._preferred_column is None else self._preferred_column
        if line == 0:
            return
        start = self._line_start(line - 1)
        self.cursor = min(start + self._preferred_column, self._line_end(start))

    def down(self) -> None:
        self._clear_selection()
        line, column = self._line_number_and_column()
        self._preferred_column = column if self._preferred_column is None else self._preferred_column
        line_count = self.text.count("\n")
        if line >= line_count:
            return
        start = self._line_start(line + 1)
        self.cursor = min(start + self._preferred_column, self._line_end(start))

    def move_left(self, *, select: bool = False) -> None:
        if select and self.selection_anchor is None:
            self.selection_anchor = self.cursor
        if not select:
            self._clear_selection()
        self.cursor = max(0, self.cursor - 1)
        self._preferred_column = None

    def move_right(self, *, select: bool = False) -> None:
        if select and self.selection_anchor is None:
            self.selection_anchor = self.cursor
        if not select:
            self._clear_selection()
        self.cursor = min(len(self.text), self.cursor + 1)
        self._preferred_column = None

    def clear(self) -> None:
        self.text = ""
        self.cursor = 0
        self._clear_selection()
        self._preferred_column = None
