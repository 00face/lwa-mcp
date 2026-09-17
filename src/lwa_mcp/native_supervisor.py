"""Native two-pane supervisor for an unmodified Codex terminal UI.

The right pane belongs entirely to Codex. LWA only owns the small controller
pane on the left and pastes finalized prompts into Codex without submitting
them, so Codex retains its own modal, completion, cursor, graphics, and input
semantics.
"""

from __future__ import annotations

import argparse
import asyncio
import curses
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from .prompt_editor import PromptEditor
from .prompt_finalizer import finalize_prompt


class NativeSupervisorUnavailable(RuntimeError):
    """Raised when the host cannot provide a real multiplexer pane."""


def _tmux() -> str:
    value = shutil.which("tmux")
    if not value:
        raise NativeSupervisorUnavailable(
            "tmux is not installed; using the low-resource curses fallback."
        )
    return value


def _run_tmux(command: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _paste_to_codex(target: str, text: str) -> None:
    tmux = _tmux()
    buffer_name = f"lwa-{os.getpid()}"
    loaded = _run_tmux([tmux, "load-buffer", "-b", buffer_name, "-"], input_text=text)
    if loaded.returncode:
        raise RuntimeError(loaded.stderr.strip() or "tmux could not load the LWA prompt")
    pasted = _run_tmux([tmux, "paste-buffer", "-b", buffer_name, "-t", target, "-d"])
    if pasted.returncode:
        raise RuntimeError(pasted.stderr.strip() or "tmux could not paste into Codex")


async def _improve_prompt(prompt: str) -> str:
    from .service import RouterService

    service = RouterService()
    await service.initialize()
    request = (
        "Improve the following user draft into a precise, complete, high-quality prompt "
        "for Codex. Preserve intent and constraints. Return only the final Codex-ready "
        "prompt, with no editing commentary.\n\nUSER DRAFT:\n"
        f"{prompt}"
    )
    prepared = await service.prepare_consensus(request)
    summary = prepared.get("preflight", {})
    if not summary.get("working_may_begin"):
        token = summary.get("confirmation_token")
        if not token:
            raise RuntimeError("LWA consensus requires an approval gate")
        service.approve_preflight(token)
    result = await service.run_prepared_task(summary["plan_token"])
    if result.get("status") != "completed":
        raise RuntimeError(str(result.get("error") or result.get("message") or "LWA consensus stopped"))
    text = str(result.get("synthesis", {}).get("text", "")).strip()
    if not text:
        raise RuntimeError("LWA consensus returned no synthesized prompt")
    return text


def _draw(screen: curses.window, feed: list[str], editor: PromptEditor, busy: bool) -> None:
    rows, columns = screen.getmaxyx()
    screen.erase()
    border = "+" + "-" * max(0, columns - 2) + "+"
    try:
        screen.addnstr(0, 0, border, max(1, columns - 1))
        screen.addnstr(1, 1, "LWA · native controller", max(1, columns - 3), curses.A_BOLD)
        screen.addnstr(2, 1, "Codex owns the right pane · review there, then press Alt+Enter", max(1, columns - 3))
        prompt_row = max(4, rows - 5)
        for index, line in enumerate(feed[-max(1, prompt_row - 4) :]):
            screen.addnstr(4 + index, 1, line, max(1, columns - 3))
        screen.addnstr(prompt_row, 1, "LWA PROMPT", max(1, columns - 3), curses.A_BOLD)
        visible = editor.text.split("\n")[-3:]
        for index, line in enumerate(visible):
            screen.addnstr(prompt_row + 1 + index, 1, ("> " if index == len(visible) - 1 else "  ") + line, max(1, columns - 3))
        screen.addnstr(rows - 2, 1, "Enter: improve + paste to Codex · Ctrl-J: newline · Ctrl-C: interrupt · Esc: exit", max(1, columns - 3))
        cursor_column = 3 + len(editor.text[: editor.cursor].split("\n")[-1])
        screen.move(min(rows - 3, prompt_row + len(visible)), min(columns - 2, cursor_column))
    except curses.error:
        pass
    screen.refresh()


async def _controller(target: str) -> int:
    feed = ["Native mode connected.", "LWA will paste reviewed prompts into the real Codex pane."]
    editor = PromptEditor()
    busy = False
    task: asyncio.Task[str] | None = None

    def draw(screen: curses.window) -> None:
        _draw(screen, feed, editor, busy)

    screen = curses.initscr()
    curses.noecho()
    curses.cbreak()
    try:
        curses.nonl()
    except curses.error:
        pass
    screen.keypad(True)
    try:
        while True:
            draw(screen)
            key = screen.get_wch()
            if key == "\x1b":
                return 0
            if key == "\x03":
                if task and not task.done():
                    task.cancel()
                    feed.append("LWA consensus cancelled.")
                    busy = False
                continue
            if key == "\n":
                editor.newline()
                continue
            if key == "\r":
                if not editor.text.strip() or busy:
                    continue
                draft = editor.text
                editor.clear()
                busy = True
                feed.append(f"LWA consensus started ({len(draft)} characters)...")
                try:
                    improved = await _improve_prompt(finalize_prompt(draft, mode="semantic").text)
                    _paste_to_codex(target, improved)
                    feed.append(f"Prompt pasted to Codex for review ({len(improved)} characters).")
                except asyncio.CancelledError:
                    feed.append("LWA consensus cancelled.")
                except Exception as exc:  # noqa: BLE001
                    feed.append(f"LWA stopped: {exc}")
                finally:
                    busy = False
                continue
            if key == "\x7f" or key == getattr(curses, "KEY_BACKSPACE", -1):
                editor.backspace()
            elif key == getattr(curses, "KEY_DC", -1):
                editor.delete()
            elif key == getattr(curses, "KEY_LEFT", -1):
                editor.left()
            elif key == getattr(curses, "KEY_RIGHT", -1):
                editor.right()
            elif key == getattr(curses, "KEY_UP", -1):
                editor.up()
            elif key == getattr(curses, "KEY_DOWN", -1):
                editor.down()
            elif isinstance(key, str) and key.isprintable():
                editor.insert(key)
    finally:
        curses.nocbreak()
        screen.keypad(False)
        curses.echo()
        curses.endwin()


def run_controller(target: str) -> int:
    return asyncio.run(_controller(target))


def run_native(codex: str, *, cwd: str | None = None) -> int:
    tmux = _tmux()
    root = str(Path(cwd or os.getcwd()).expanduser().resolve())
    session = f"lwa-{os.getpid()}"
    target = f"{session}:0.1"
    controller = shlex.join([sys.executable, "-m", "lwa_mcp.native_supervisor", "--controller", "--target", target])
    codex_command = shlex.join([codex])
    try:
        created = _run_tmux([tmux, "new-session", "-d", "-s", session, "-x", "160", "-y", "48", "-c", root, controller])
        if created.returncode:
            raise NativeSupervisorUnavailable(created.stderr.strip() or "tmux could not create the LWA session")
        split = _run_tmux([tmux, "split-window", "-h", "-p", "68", "-t", f"{session}:0.0", "-c", root, codex_command])
        if split.returncode:
            raise NativeSupervisorUnavailable(split.stderr.strip() or "tmux could not create the Codex pane")
        for option, value in (
            ("mouse", "on"),
            ("pane-border-status", "top"),
            ("pane-border-format", " LWA native · #{pane_index} "),
        ):
            _run_tmux([tmux, "set-option", "-t", session, option, value])
        attached = subprocess.run([tmux, "attach-session", "-t", session], check=False)
        return attached.returncode
    finally:
        _run_tmux([tmux, "kill-session", "-t", session])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controller", action="store_true")
    parser.add_argument("--target")
    args = parser.parse_args()
    if not args.controller or not args.target:
        parser.error("controller mode requires --target")
    raise SystemExit(run_controller(args.target))
