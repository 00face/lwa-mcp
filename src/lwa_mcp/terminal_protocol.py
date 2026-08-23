"""Bounded terminal capability and visible-text helpers shared by Lwa surfaces."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass

_OSC_RE = re.compile(r"\x1b\][^\x07]*(?:\x07|\x1b\\)")
_CSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_GRAPHICS_RE = re.compile(r"\x1b(?:_G|Pq)[^\x1b]*(?:\x1b\\)")
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)(\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth(?:orization)?|password|passwd|secret|token)\b\s*[:=]\s*)([^\s,;\"'}]+)"
)
_BEARER_RE = re.compile(r"(?i)(\bbearer\s+)[A-Za-z0-9._~+/=-]+")
_TOKEN_RE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,}|xox[baprs]-[A-Za-z0-9-]{16,}|AIza[A-Za-z0-9_-]{20,})\b")
_OPAQUE_PAYLOAD_RE = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{256,}={0,2}(?![A-Za-z0-9+/])")


@dataclass(frozen=True, slots=True)
class TerminalCapabilities:
    renderer: str
    ansi_vt: bool = True
    unicode: bool = True
    osc8_hyperlinks: bool = True
    kitty_graphics: bool = False
    sixel_graphics: bool = False
    image_fallback: str = "text-placeholder"

    def public_json(self) -> dict[str, object]:
        return {
            "renderer": self.renderer,
            "ansi_vt": self.ansi_vt,
            "unicode": self.unicode,
            "osc8_hyperlinks": self.osc8_hyperlinks,
            "kitty_graphics": self.kitty_graphics,
            "sixel_graphics": self.sixel_graphics,
            "image_fallback": self.image_fallback,
        }


def detect_terminal_capabilities(env: Mapping[str, str] | None = None) -> TerminalCapabilities:
    values = env if env is not None else os.environ
    term = values.get("TERM", "").lower()
    program = values.get("TERM_PROGRAM", "").lower()
    ghostty = program == "ghostty" or bool(values.get("GHOSTTY_RESOURCES_DIR"))
    kitty = "kitty" in term or bool(values.get("KITTY_WINDOW_ID"))
    sixel = "sixel" in term or "sixel" in values.get("COLORTERM", "").lower()
    if ghostty:
        renderer = "ghostty-host / Lwa fallback frame"
    elif kitty:
        renderer = "kitty-host / Lwa fallback frame"
    else:
        renderer = "curses fallback frame"
    return TerminalCapabilities(
        renderer=renderer,
        kitty_graphics=kitty,
        sixel_graphics=sixel,
    )


def graphics_renderer(surface: str, env: Mapping[str, str] | None = None) -> str:
    """Select an honest graphics path for a native or browser surface."""
    capabilities = detect_terminal_capabilities(env)
    if surface == "web":
        return "browser-image-gate-pending"
    if capabilities.kitty_graphics or "ghostty" in capabilities.renderer.lower():
        return "kitty-or-ghostty"
    if capabilities.sixel_graphics:
        return "sixel"
    return "text-fallback"


def visible_text(data: str) -> str:
    """Remove terminal controls while preserving readable Unicode and links."""
    data = _GRAPHICS_RE.sub("[graphics omitted]", data)
    return _CSI_RE.sub("", _OSC_RE.sub("", data))


class TerminalStreamFilter:
    """Strip split ANSI/OSC/Kitty/Sixel sequences without leaking their payload."""

    def __init__(self) -> None:
        self._pending = ""

    def feed(self, data: str, *, final: bool = False) -> str:
        value = self._pending + data
        self._pending = ""
        output: list[str] = []
        index = 0
        while index < len(value):
            if value[index] != "\x1b":
                output.append(value[index])
                index += 1
                continue
            if index + 1 >= len(value):
                self._pending = value[index:]
                break
            kind = value[index + 1]
            if kind in "]_P":
                end = value.find("\x07" if kind == "]" else "\x1b\\", index + 2)
                if end < 0:
                    if not final:
                        self._pending = value[index:]
                    break
                # Graphics are intentionally omitted from the text-only LWA
                # surfaces; repeated placeholders make the fallback unreadable.
                output.append("")
                index = end + (1 if kind == "]" and value[end] == "\x07" else 2)
                continue
            if kind == "[":
                match = re.search(r"[@-~]", value[index + 2 :])
                if match is None:
                    if not final:
                        self._pending = value[index:]
                    break
                index += 2 + match.end()
                continue
            # Drop a standalone escape and its one-byte command.
            index += 2
        if final:
            self._pending = ""
        return "".join(output)


class TerminalTextBuffer:
    """Small text-mode terminal buffer for the LWA fallback frame.

    Codex redraws status lines with carriage returns. Splitting every PTY
    chunk with ``str.splitlines()`` turns those redraws into one-word lines.
    This buffer applies the text controls needed by the fallback renderer
    while deliberately leaving full graphical terminal emulation to Ghostty.
    """

    def __init__(self, max_lines: int = 1200) -> None:
        self.lines = [""]
        self.cursor_column = 0
        self.max_lines = max(20, max_lines)

    def feed(self, data: str) -> list[str]:
        for char in data:
            if char == "\r":
                self.cursor_column = 0
            elif char == "\n":
                self.lines.append("")
                self.cursor_column = 0
            elif char == "\b":
                self.cursor_column = max(0, self.cursor_column - 1)
            elif char == "\t":
                spaces = 8 - (self.cursor_column % 8)
                self._write(" " * spaces)
            elif char.isprintable() or char == "\u00a0":
                self._write(char)
        if len(self.lines) > self.max_lines:
            del self.lines[: len(self.lines) - self.max_lines]
        return self.lines

    def _write(self, text: str) -> None:
        line = self.lines[-1]
        if self.cursor_column > len(line):
            line += " " * (self.cursor_column - len(line))
        end = self.cursor_column + len(text)
        self.lines[-1] = line[: self.cursor_column] + text + line[end:]
        self.cursor_column = end


def redact_terminal_text(data: str) -> str:
    """Mask credential-shaped terminal content before it reaches LWA surfaces."""
    data = _BEARER_RE.sub(r"\1[REDACTED]", data)
    data = _SECRET_ASSIGNMENT_RE.sub(r"\1[REDACTED]", data)
    data = _TOKEN_RE.sub("[REDACTED]", data)
    return _OPAQUE_PAYLOAD_RE.sub("[OPAQUE PAYLOAD REDACTED]", data)
