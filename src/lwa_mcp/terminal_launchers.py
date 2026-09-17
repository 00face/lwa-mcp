"""Host-specific terminal launch helpers for the native LWA/Codex layout."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TerminalLaunchPlan:
    """Describe how to open the Codex bridge for the current host."""

    launcher: str
    mode: str
    command: list[str]
    cwd: str
    capabilities: TerminalCapabilities | None = None
    process: subprocess.Popen | None = None


@dataclass(frozen=True, slots=True)
class TerminalCapabilities:
    """Redacted, user-visible host capabilities used for launch decisions."""

    terminal: str
    executable: str
    mode: str
    graphics: bool
    mouse: bool
    clipboard: bool
    accessible_text: bool = True


_KNOWN_TERMINALS = (
    "ghostty",
    "alacritty",
    "kitty",
    "wezterm",
    "tabby",
    "wave",
    "gnome-terminal",
    "konsole",
    "terminator",
    "guake",
    "lxterminal",
    "cool-retro-term",
    "terminus",
    "rio",
    "blackbox",
    "ptyxis",
    "tmux",
    "yakuake",
    "sakura",
    "lilyterm",
    "xfce4-terminal",
    "ratty",
    "tilda",
)


def _terminal_override() -> str | None:
    value = os.environ.get("LWA_TERMINAL_ADAPTER", "").strip().lower()
    if not value:
        return None
    if value not in _KNOWN_TERMINALS and value not in {"x-terminal-emulator", "xterm"}:
        raise RuntimeError(
            f"Unknown LWA_TERMINAL_ADAPTER={value!r}. Choose a supported terminal adapter."
        )
    return value


def _preferred_hosts(env: dict[str, str]) -> list[str]:
    hosts: list[str] = []
    if env.get("TMUX"):
        hosts.append("tmux")
    if env.get("TERM_PROGRAM", "").lower() == "ghostty" or env.get("GHOSTTY_RESOURCES_DIR"):
        hosts.append("ghostty")
    if env.get("WEZTERM_PANE"):
        hosts.append("wezterm")
    if env.get("KITTY_WINDOW_ID") or env.get("KITTY_LISTEN_ON"):
        hosts.append("kitty")
    if env.get("GNOME_TERMINAL_SCREEN") or env.get("GNOME_TERMINAL_SERVICE"):
        hosts.append("gnome-terminal")
    if env.get("KONSOLE_VERSION"):
        hosts.append("konsole")
    if env.get("TERMINATOR_UUID"):
        hosts.append("terminator")
    if env.get("ALACRITTY_WINDOW_ID") or env.get("ALACRITTY_LOG"):
        hosts.append("alacritty")
    if env.get("TABBY_CONFIG_DIRECTORY"):
        hosts.append("tabby")
    if env.get("WAVE_TERMINAL") or env.get("WAVE_VERSION"):
        hosts.append("wave")
    return hosts


def _find_terminal() -> tuple[str, str]:
    override = _terminal_override()
    candidates = [override] if override else []
    candidates.extend(_preferred_hosts(dict(os.environ)))
    candidates.extend(_KNOWN_TERMINALS)
    candidates.extend(["x-terminal-emulator", "xterm"])
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        executable = shutil.which(candidate)
        if executable:
            return candidate, executable
    raise RuntimeError(
        "No supported terminal launcher was found. LWA requires either pane control "
        "or a second terminal window. Install a supported GUI terminal or set "
        "LWA_TERMINAL_ADAPTER explicitly."
    )


def _python_module_command(module: str, *args: str) -> list[str]:
    return [sys.executable, "-m", module, *args]


def _codex_bridge_command(*, socket_path: str, cwd: str, codex: str | None, disable_lwa_mcp: bool) -> list[str]:
    command = _python_module_command(
        "lwa_mcp.codex_bridge",
        "--socket",
        socket_path,
        "--cwd",
        cwd,
    )
    if codex:
        command.extend(["--codex", codex])
    if disable_lwa_mcp:
        command.append("--disable-lwa-mcp")
    return command


def _launcher_command(
    executable: str,
    *,
    cwd: str,
    bridge_command: list[str],
) -> tuple[str, list[str]]:
    base = Path(executable).name.lower()
    if base == "wezterm" and os.environ.get("WEZTERM_PANE"):
        return (
            "wezterm-split",
            [
                executable,
                "cli",
                "split-pane",
                "--cwd",
                cwd,
                "--",
                *bridge_command,
            ],
        )
    if base == "kitty" and os.environ.get("KITTY_LISTEN_ON"):
        return (
            "kitty-split",
            [
                executable,
                "@",
                "launch",
                "--location=vsplit",
                "--cwd",
                cwd,
                "--",
                *bridge_command,
            ],
        )
    if base == "ghostty":
        return (
            "ghostty-window",
            [
                executable,
                "+new-window",
                "--working-directory",
                cwd,
                "--",
                *bridge_command,
            ],
        )
    if base == "kitty":
        return (
            "kitty-window",
            [
                executable,
                "--directory",
                cwd,
                *bridge_command,
            ],
        )
    if base == "gnome-terminal":
        return (
            "gnome-terminal-window",
            [
                executable,
                "--working-directory",
                cwd,
                "--",
                *bridge_command,
            ],
        )
    if base == "konsole":
        return (
            "konsole-window",
            [
                executable,
                "--workdir",
                cwd,
                "-e",
                *bridge_command,
            ],
        )
    if base == "terminator":
        return (
            "terminator-window",
            [
                executable,
                "--working-directory",
                cwd,
                "-x",
                *bridge_command,
            ],
        )
    if base == "alacritty":
        return (
            "alacritty-window",
            [
                executable,
                "--working-directory",
                cwd,
                "-e",
                *bridge_command,
            ],
        )
    if base == "guake":
        return (
            "guake-window",
            [
                executable,
                "-e",
                *bridge_command,
            ],
        )
    if base in {"lxterminal", "cool-retro-term", "terminus", "sakura", "lilyterm", "xfce4-terminal", "ratty"}:
        return (
            f"{base}-window",
            [
                executable,
                "--working-directory",
                cwd,
                "-e",
                *bridge_command,
            ],
        )
    if base == "tmux" and os.environ.get("TMUX"):
        target = os.environ.get("TMUX_PANE")
        target_args = ["-t", target] if target else []
        return (
            "tmux-split",
            [
                executable,
                "split-window",
                "-h",
                *target_args,
                "-c",
                cwd,
                "--",
                *bridge_command,
            ],
        )
    if base in {"yakuake", "tilda"}:
        return (
            f"{base}-window",
            [executable, "-e", shlex.join(bridge_command)],
        )
    if base in {"rio", "blackbox", "ptyxis", "wave", "tabby"}:
        return (
            f"{base}-window",
            [executable, "--working-directory", cwd, "--", *bridge_command],
        )
    if base == "tabby":
        return (
            "tabby-window",
            [
                executable,
                "--",
                *bridge_command,
            ],
        )
    if base == "wave":
        return (
            "wave-window",
            [
                executable,
                "--",
                *bridge_command,
            ],
        )
    if shutil.which("x-terminal-emulator"):
        return (
            "x-terminal-emulator",
            [
                "x-terminal-emulator",
                "-e",
                *bridge_command,
            ],
        )
    if shutil.which("xterm"):
        return (
            "xterm",
            [
                "xterm",
                "-e",
                *bridge_command,
            ],
        )
    raise RuntimeError(
        "No supported terminal launcher was found. Install a supported GUI terminal "
        "or use a host that can open a second window."
    )


def launch_codex_bridge(
    *,
    socket_path: str,
    cwd: str,
    codex: str | None,
    disable_lwa_mcp: bool,
) -> TerminalLaunchPlan:
    """Launch the Codex bridge using the verified split/window host contract."""

    terminal, executable = _find_terminal()
    bridge_command = _codex_bridge_command(
        socket_path=socket_path,
        cwd=cwd,
        codex=codex,
        disable_lwa_mcp=disable_lwa_mcp,
    )
    launcher, command = _launcher_command(
        executable,
        cwd=cwd,
        bridge_command=bridge_command,
    )
    mode = "split" if launcher in {"wezterm-split", "kitty-split", "tmux-split"} else "window"
    capabilities = TerminalCapabilities(
        terminal=terminal,
        executable=executable,
        mode=mode,
        graphics=terminal in {"ghostty", "kitty", "wezterm"},
        mouse=True,
        clipboard=True,
    )
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return TerminalLaunchPlan(
        launcher=launcher,
        mode=mode,
        command=command,
        cwd=cwd,
        capabilities=capabilities,
        process=process,
    )
