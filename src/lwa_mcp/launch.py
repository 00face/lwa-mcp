"""Cross-platform launchers for the Lwa terminal and web surfaces."""

from __future__ import annotations

import argparse
import os
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import webbrowser
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlencode

from .config import load_config
from .service import RouterService
from .terminal_launchers import launch_codex_bridge


def _record_launch_failure(application: str, exc: BaseException) -> Path | None:
    try:
        from .debug_log import write_startup_error

        return write_startup_error(application, exc)
    except Exception:  # noqa: BLE001
        return None


def _record_launch_event(application: str, event: str) -> None:
    with suppress(Exception):
        from .debug_log import write_startup_event

        write_startup_event(application, event)


def _codex_executable() -> str:
    executable = shutil.which("codex")
    if executable is None:
        raise RuntimeError("Codex was not found on PATH. Install Codex or pass --codex.")
    return executable


def _dashboard_url() -> str:
    settings = load_config().settings
    return f"http://{settings.dashboard_host}:{settings.dashboard_port}"


def _dashboard_ready() -> bool:
    settings = load_config().settings
    return RouterService._dashboard_running(settings.dashboard_host, settings.dashboard_port)


def _start_dashboard() -> None:
    if _dashboard_ready():
        return
    executable = shutil.which("lwa-dashboard")
    if executable is None:
        candidate = Path(sys.executable).with_name("lwa-dashboard")
        if candidate.exists():
            executable = str(candidate)
    if executable is None:
        raise RuntimeError("lwa-dashboard was not found. Install the Lwa environment first.")
    subprocess.Popen(
        [executable],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if _dashboard_ready():
            return
        time.sleep(0.1)
    raise RuntimeError(f"Lwa web service did not become ready at {_dashboard_url()}.")


def launch_codex(args: argparse.Namespace) -> int:
    _start_dashboard()
    executable = args.codex or _codex_executable()
    command = [executable]
    if args.no_alt_screen:
        command.append("--no-alt-screen")
    command.extend(args.codex_args)
    return subprocess.run(command, check=False).returncode


def _maybe_bootstrap_ghostty_split(args: argparse.Namespace) -> int | None:
    """Run LWA inside tmux so Linux Ghostty gets a real same-window split."""
    if os.environ.get("LWA_TMUX_BOOTSTRAPPED") or os.environ.get("TMUX"):
        return None
    if os.environ.get("LWA_GHOSTTY_SPLIT", "auto").lower() == "window":
        return None
    if os.environ.get("TERM_PROGRAM", "").lower() != "ghostty" and not os.environ.get("GHOSTTY_RESOURCES_DIR"):
        return None
    tmux = shutil.which("tmux")
    if tmux is None:
        return None
    session = f"lwa-{os.getpid()}"
    nested = [sys.executable, "-m", "lwa_mcp.launch", "frame"]
    if args.codex:
        nested.extend(["--codex", args.codex])
    command = [
        tmux,
        "new-session",
        "-A",
        "-s",
        session,
        "-c",
        str(Path.cwd()),
        shlex.join(nested),
    ]
    environment = os.environ.copy()
    # Do not leak a pane identity from the parent terminal/session into the
    # newly created tmux server. tmux will assign the child its real
    # TMUX/TMUX_PANE values; inheriting these can target an older session.
    environment.pop("TMUX", None)
    environment.pop("TMUX_PANE", None)
    environment["LWA_TMUX_BOOTSTRAPPED"] = "1"
    result = subprocess.run(command, check=False, env=environment, capture_output=True, text=True)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"tmux exited with status {result.returncode}"
        raise RuntimeError(f"Ghostty tmux bootstrap failed: {detail}")
    return result.returncode


def _native_tmux_split_enabled() -> bool:
    """Return whether this process can create the authoritative Codex pane."""
    return bool(os.environ.get("TMUX")) and os.environ.get("LWA_NATIVE_SPLIT", "auto").lower() != "window"


def _install_native_focus_bindings(*, tmux: str, lwa_pane: str, codex_pane: str) -> list[list[str]]:
    """Install explicit Alt-arrow native pane focus bindings.

    The command is passed as argv to tmux; no shell interpolation is involved.
    Alt+Left selects LWA and Alt+Right selects Codex. No synthetic key is
    delivered to the destination, and Tab remains available to the prompt.
    """
    # A previous LWA process may have exited before its finally block ran.
    # Clear all legacy navigation bindings before installing the new contract.
    _clear_native_focus_navigation_bindings(tmux=tmux)
    commands: list[list[str]] = []
    for key, target in (("M-Left", lwa_pane), ("M-Right", codex_pane)):
        command = [
            tmux,
            "bind-key",
            "-T",
            "root",
            key,
            "select-pane",
            "-t",
            target,
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        commands.append(command)
    _record_launch_event(
        "lwa-focus",
        f"transport_bindings_ready lwa={lwa_pane} codex={codex_pane} keys=M-Left,M-Right",
    )
    return commands


def _clear_native_focus_navigation_bindings(*, tmux: str) -> None:
    """Remove every pane-navigation binding from older LWA launches."""
    for key in ("M-Left", "M-Right", "Tab", "BTab", "C-i"):
        subprocess.run(
            [tmux, "unbind-key", "-T", "root", key],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def _cleanup_native_focus_bindings(*, tmux: str) -> None:
    """Remove only the root bindings owned by the current LWA launch."""
    for key in ("M-Left", "M-Right", "Tab", "BTab", "C-i", "C-q", "C-c"):
        subprocess.run(
            [tmux, "unbind-key", "-T", "root", key],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def _launch_native_tmux_codex(*, codex: str, cwd: str) -> str:
    """Create a visible Codex pane and return its authoritative pane ID."""
    tmux = shutil.which("tmux")
    if tmux is None:
        raise RuntimeError("tmux is unavailable for native split mode")
    command = [
        "env",
        "-u",
        "TMUX",
        "-u",
        "TMUX_PANE",
        "TERM=xterm-ghostty",
        "TERM_PROGRAM=ghostty",
        codex,
        "--no-alt-screen",
    ]
    # Codex intentionally suppresses its native pet renderer under tmux, and
    # its /pets overlay can still attempt pane-unsafe graphics. LWA owns the
    # reliable Codex-side mirror in this mode, so keep the native Codex pet
    # disabled by default. Operators can opt back in for experimentation.
    if os.environ.get("LWA_NATIVE_CODEX_PET", "off").lower() not in {"1", "true", "yes", "on"}:
        command.extend(["-c", 'tui.pet=""'])
    # Native mode runs LWA in its own pane, so Codex must retain its normal
    # plugin/module configuration.  The old bridge safeguard disabled the
    # LWA plugin here as well, which made Codex report that the LWA module was
    # unavailable.  Keep an explicit escape hatch for installations whose
    # plugin startup is independently broken; it is opt-in rather than the
    # native default.
    if os.environ.get("LWA_NATIVE_DISABLE_MCP", "0").lower() in {"1", "true", "yes", "on"}:
        command.extend(["-c", 'plugins."lwa-mcp@armando-local".enabled=false'])
    target = os.environ.get("TMUX_PANE")
    target_args = ["-t", target] if target else []
    # Open graphics passthrough before Codex starts. Codex may emit its pet
    # and other startup images immediately during TUI initialization. The
    # terminal graphics namespace is shared by tmux and its panes, so the
    # native Codex pane must own this path; LWA does not mirror it.
    for option, value in (
        ("mouse", "on"),
        ("allow-passthrough", "on"),
        ("status", "off"),
        ("set-clipboard", "on"),
        ("extended-keys", "on"),
    ):
        subprocess.run(
            [tmux, "set-option", "-g", option, value],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    # Advertise the actual Ghostty terminal capabilities to the child pane.
    # Without this, tmux can downgrade the pane to a conservative terminal
    # profile and Codex correctly suppresses native pet graphics.
    subprocess.run(
        [tmux, "set-option", "-as", "terminal-features", ",xterm-ghostty:RGB,hyperlinks"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    result = subprocess.run(
        [
            tmux,
            "split-window",
            "-h",
            "-l",
            "60%",
            "-P",
            "-F",
            "#{pane_id}",
            *target_args,
            "-c",
            cwd,
            "--",
            *command,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        detail = result.stderr.strip() or "tmux did not return a pane identity"
        raise RuntimeError(f"native Codex split failed: {detail}")
    pane_id = result.stdout.strip().splitlines()[-1]
    # Tab is a pane-focus handshake in native mode. Do not use
    # `select-pane -l`: graphics and mouse activity can change tmux's last-pane
    # history and strand focus in a scrolled Codex overlay. Toggle explicitly
    # between the controller pane and the authoritative Codex pane.
    lwa_pane = target or os.environ.get("TMUX_PANE")
    if lwa_pane:
        _install_native_focus_bindings(tmux=tmux, lwa_pane=lwa_pane, codex_pane=pane_id)
    # Ctrl+Q is the explicit combined-surface exit. The native split owns
    # this tmux window, so closing it terminates both LWA and Codex together.
    subprocess.run(
        [tmux, "bind-key", "-T", "root", "C-q", "kill-window"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    # Native Codex owns its PTY, so intercept Ctrl+C at tmux level. Capture
    # the active pane instead of forwarding an interrupt to Codex. This keeps
    # Ctrl+C safe in both native panes; the embedded LWA frame uses its more
    # precise selection-aware copy handler.
    clipboard = (
        "xclip -selection clipboard"
        if shutil.which("xclip")
        else "wl-copy"
        if shutil.which("wl-copy")
        else "xsel --clipboard --input"
        if shutil.which("xsel")
        else "cat >/dev/null"
    )
    copy_command = f"tmux capture-pane -p -t {pane_id} -S - | {clipboard}"
    # C-c is source-aware: only Codex is captured by tmux. LWA receives its
    # own C-c so the curses panel can copy the local selection/prompt.
    copy_or_forward = [
        "if-shell",
        "-F",
        f"#{'{'}pane_id{'}'} == {pane_id}",
        f"run-shell -b '{copy_command}'",
        f"send-keys -t {lwa_pane or pane_id} C-c",
    ]
    subprocess.run(
        [tmux, "bind-key", "-T", "root", "C-c", *copy_or_forward],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    _record_launch_event("lwa-focus", f"bindings_ready lwa={lwa_pane or 'unknown'} codex={pane_id}")
    return pane_id


def launch_frame(args: argparse.Namespace) -> int:
    if getattr(args, "fallback", False):
        try:
            from .terminal_frame import run

            return run(args.codex)
        except (ImportError, RuntimeError):
            executable = args.codex or _codex_executable()
            return subprocess.run([executable], check=False).returncode

    _record_launch_event("lwa-launcher", "launch_frame")
    try:
        bootstrapped = _maybe_bootstrap_ghostty_split(args)
    except (OSError, RuntimeError) as exc:
        path = _record_launch_failure("lwa-launcher", exc)
        print(f"Lwa launch failed: {exc}", file=sys.stderr)
        if path:
            print(f"Lwa startup log: {path}", file=sys.stderr)
        return 1
    if bootstrapped is not None:
        return bootstrapped

    bridge_socket: Path | None = None
    plan = None
    try:
        from .terminal_frame import run

        codex = args.codex or _codex_executable()
        if _native_tmux_split_enabled():
            pane_id = _launch_native_tmux_codex(codex=codex, cwd=str(Path.cwd()))
            try:
                return run(codex, native_tmux_pane=pane_id)
            finally:
                with suppress(OSError, subprocess.CalledProcessError):
                    _cleanup_native_focus_bindings(tmux=shutil.which("tmux") or "tmux")
                # The session owns the pane and removes it during close. This
                # fallback only handles a failure before the TUI starts.
                if pane_id:
                    with suppress(OSError, subprocess.CalledProcessError):
                        subprocess.run(
                            [shutil.which("tmux") or "tmux", "kill-pane", "-t", pane_id],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=True,
                        )
        bridge_root = Path(tempfile.gettempdir()) / "lwa-mcp"
        bridge_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            bridge_root.chmod(0o700)
        except OSError:
            pass
        bridge_socket = bridge_root / f"codex-bridge-{secrets.token_hex(8)}.sock"
        plan = launch_codex_bridge(
            socket_path=str(bridge_socket),
            cwd=str(Path.cwd()),
            codex=codex,
            disable_lwa_mcp=True,
        )
        return run(codex, bridge_socket=str(bridge_socket))
    except ImportError:
        executable = args.codex or _codex_executable()
        return subprocess.run([executable], check=False).returncode
    except RuntimeError as exc:
        if plan is not None and plan.process is not None and plan.process.poll() is None:
            try:
                plan.process.terminate()
                plan.process.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    plan.process.kill()
                except OSError:
                    pass
        path = _record_launch_failure("lwa-launcher", exc)
        print(f"Lwa native mode unavailable: {exc}", file=sys.stderr)
        if path:
            print(f"Lwa startup log: {path}", file=sys.stderr)
        return 1
    finally:
        if bridge_socket is not None and bridge_socket.exists():
            try:
                bridge_socket.unlink()
            except OSError:
                pass


def launch_web(args: argparse.Namespace) -> int:
    _start_dashboard()
    url = _dashboard_url() + "/codex?" + urlencode({"cwd": str(Path.cwd())})
    print(f"Lwa web interface: {url}")
    if not args.no_browser:
        webbrowser.open(url)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lwa", description="Launch the Lwa terminal or web surface.")
    sub = parser.add_subparsers(dest="command")

    terminal = sub.add_parser("codex", help="Start Codex inside the Lwa terminal frame")
    terminal.add_argument("--codex", help="Explicit Codex executable")
    terminal.add_argument("--no-alt-screen", action="store_true")
    terminal.add_argument("codex_args", nargs=argparse.REMAINDER)

    frame = sub.add_parser("frame", help="Start the low-resource Lwa terminal frame")
    frame.add_argument("--codex", help="Explicit Codex executable")
    frame.add_argument("--fallback", action="store_true", help="Use the curses compatibility frame")

    web = sub.add_parser("web", help="Start the Lwa web surface")
    web.add_argument("--no-browser", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    command = args.command or "frame"
    if command == "frame":
        if not hasattr(args, "codex"):
            args.codex = None
        if not hasattr(args, "fallback"):
            args.fallback = False
        raise SystemExit(launch_frame(args))
    if command == "codex":
        if not hasattr(args, "codex"):
            args.codex = None
            args.no_alt_screen = False
            args.codex_args = []
        raise SystemExit(launch_codex(args))
    if command == "web":
        raise SystemExit(launch_web(args))
    parser.error(f"unknown command: {command}")


def web_main() -> None:
    parser = argparse.ArgumentParser(prog="lwa-web", description="Launch the Lwa web surface.")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    raise SystemExit(launch_web(args))


if __name__ == "__main__":
    main()
