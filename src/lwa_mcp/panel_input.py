"""Semantic input routing independent of curses key constants."""

from __future__ import annotations

from enum import StrEnum


class InputAction(StrEnum):
    TEXT = "text"
    FOCUS_NEXT = "focus_next"
    FOCUS_PREVIOUS = "focus_previous"
    EXIT = "exit"
    COPY = "copy"
    SUBMIT = "submit"
    NEWLINE = "newline"


def route_key(value: object) -> InputAction:
    """Return the stable action for a raw terminal value.

    Unrecognized values remain text-or-navigation work for the existing
    editor path; this router only owns global panel actions.
    """
    if value in ("\t", 9, "__LWA_TAB__"):
        return InputAction.FOCUS_NEXT
    if value in ("__LWA_SHIFT_TAB__", "KEY_BTAB"):
        return InputAction.FOCUS_PREVIOUS
    if value in ("\x11", 17, "__LWA_EXIT__"):
        return InputAction.EXIT
    if value in ("\x03",):
        return InputAction.COPY
    if value in ("\r", "__LWA_SUBMIT__"):
        return InputAction.SUBMIT
    if value in ("\n",):
        return InputAction.NEWLINE
    return InputAction.TEXT
