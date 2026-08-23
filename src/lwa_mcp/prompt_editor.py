"""Small multiline line editor for the native LWA terminal frame."""

from __future__ import annotations


class PromptEditor:
    """Cursor-aware, dependency-free multiline prompt buffer."""

    def __init__(self) -> None:
        self.text = ""
        self.cursor = 0
        self._preferred_column: int | None = None

    def insert(self, value: str) -> None:
        self.text = self.text[: self.cursor] + value + self.text[self.cursor :]
        self.cursor += len(value)
        self._preferred_column = None

    def newline(self) -> None:
        self.insert("\n")

    def backspace(self) -> None:
        if self.cursor:
            self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
            self.cursor -= 1
        self._preferred_column = None

    def delete(self) -> None:
        if self.cursor < len(self.text):
            self.text = self.text[: self.cursor] + self.text[self.cursor + 1 :]
        self._preferred_column = None

    def left(self) -> None:
        self.cursor = max(0, self.cursor - 1)
        self._preferred_column = None

    def right(self) -> None:
        self.cursor = min(len(self.text), self.cursor + 1)
        self._preferred_column = None

    def _line_bounds(self) -> tuple[int, int]:
        start = self.text.rfind("\n", 0, self.cursor) + 1
        end = self.text.find("\n", self.cursor)
        return start, len(self.text) if end < 0 else end

    def home(self) -> None:
        self.cursor = self._line_bounds()[0]
        self._preferred_column = None

    def end(self) -> None:
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
        line, column = self._line_number_and_column()
        self._preferred_column = column if self._preferred_column is None else self._preferred_column
        if line == 0:
            return
        start = self._line_start(line - 1)
        self.cursor = min(start + self._preferred_column, self._line_end(start))

    def down(self) -> None:
        line, column = self._line_number_and_column()
        self._preferred_column = column if self._preferred_column is None else self._preferred_column
        line_count = self.text.count("\n")
        if line >= line_count:
            return
        start = self._line_start(line + 1)
        self.cursor = min(start + self._preferred_column, self._line_end(start))

    def clear(self) -> None:
        self.text = ""
        self.cursor = 0
        self._preferred_column = None
