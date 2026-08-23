from __future__ import annotations

from types import SimpleNamespace


def test_launch_codex_starts_dashboard_and_preserves_codex_arguments(monkeypatch):
    from lwa_mcp import launch

    calls = []
    monkeypatch.setattr(launch, "_start_dashboard", lambda: calls.append("dashboard"))
    monkeypatch.setattr(
        launch.subprocess,
        "run",
        lambda command, check=False: calls.append(command) or SimpleNamespace(returncode=7),
    )

    args = SimpleNamespace(
        codex=None,
        no_alt_screen=True,
        codex_args=["hello", "world"],
    )
    monkeypatch.setattr(launch, "_codex_executable", lambda: "codex-test")

    assert launch.launch_codex(args) == 7
    assert calls == ["dashboard", ["codex-test", "--no-alt-screen", "hello", "world"]]


def test_launch_web_starts_dashboard_and_opens_browser(monkeypatch, capsys):
    from lwa_mcp import launch

    calls = []
    monkeypatch.setattr(launch, "_start_dashboard", lambda: calls.append("dashboard"))
    monkeypatch.setattr(launch, "_dashboard_url", lambda: "http://127.0.0.1:8766")
    monkeypatch.setattr(launch.webbrowser, "open", lambda url: calls.append(url))

    args = SimpleNamespace(no_browser=False)
    assert launch.launch_web(args) == 0
    assert calls[0] == "dashboard"
    assert calls[1].startswith("http://127.0.0.1:8766/codex?cwd=")
    assert "Lwa web interface: http://127.0.0.1:8766/codex?cwd=" in capsys.readouterr().out


def test_web_main_can_skip_browser(monkeypatch):
    from lwa_mcp import launch

    calls = []
    monkeypatch.setattr(launch, "launch_web", lambda args: calls.append(args) or 0)
    monkeypatch.setattr(launch.sys, "argv", ["lwa-web", "--no-browser"])

    try:
        launch.web_main()
    except SystemExit as exc:
        assert exc.code == 0

    assert calls[0].no_browser is True


def test_bare_lwa_defaults_to_codex(monkeypatch):
    from lwa_mcp import launch

    calls = []
    monkeypatch.setattr(launch, "launch_frame", lambda args: calls.append(args) or 0)
    monkeypatch.setattr(launch.sys, "argv", ["lwa"])

    try:
        launch.main()
    except SystemExit as exc:
        assert exc.code == 0

    assert calls[0].codex is None


def test_launch_frame_uses_bridge_and_controller(monkeypatch):
    from lwa_mcp import launch

    calls = []
    monkeypatch.setattr(launch, "_codex_executable", lambda: "codex-test")
    monkeypatch.setattr(launch, "launch_codex_bridge", lambda **kwargs: calls.append(("bridge", kwargs)) or None)
    monkeypatch.setattr("lwa_mcp.terminal_frame.run", lambda executable, *, bridge_socket=None: calls.append(("frame", executable, bridge_socket)) or 0)
    monkeypatch.setattr(launch.tempfile, "gettempdir", lambda: "/tmp")
    monkeypatch.setattr(launch.secrets, "token_hex", lambda _n: "bridge-token")

    monkeypatch.setenv("TERM_PROGRAM", "ghostty")
    monkeypatch.setattr(launch.shutil, "which", lambda name: "/usr/bin/ghostty" if name == "ghostty" else None)

    args = type("Args", (), {"codex": None, "fallback": False})()
    assert launch.launch_frame(args) == 0
    assert calls[0][0] == "bridge"
    assert calls[0][1]["codex"] == "codex-test"
    assert calls[1][0] == "frame"
    assert calls[1][1] == "codex-test"
    assert calls[1][2].endswith("bridge-token.sock")


def test_launch_frame_fallback_is_explicit(monkeypatch):
    from lwa_mcp import launch

    calls = []
    monkeypatch.setattr(launch, "_codex_executable", lambda: "codex-test")
    monkeypatch.setattr("lwa_mcp.terminal_frame.run", lambda executable, *, bridge_socket=None: calls.append(("fallback", executable, bridge_socket)) or 0)
    args = type("Args", (), {"codex": None, "fallback": True})()
    assert launch.launch_frame(args) == 0
    assert calls == [("fallback", None, None)]


def test_terminal_bridge_requires_supported_launcher(monkeypatch):
    from lwa_mcp import terminal_launchers

    monkeypatch.setattr(terminal_launchers.shutil, "which", lambda name: None)
    monkeypatch.setattr(terminal_launchers.os, "environ", {})
    try:
        terminal_launchers.launch_codex_bridge(
            socket_path="/tmp/lwa.sock",
            cwd="/tmp",
            codex="codex-test",
            disable_lwa_mcp=True,
        )
    except RuntimeError as exc:
        assert "second terminal window" in str(exc)
    else:  # pragma: no cover - assertion branch
        raise AssertionError("missing launcher must fail clearly")


def test_terminal_bridge_prefers_current_host(monkeypatch):
    from lwa_mcp import terminal_launchers

    launches = []

    def which(name):
        return f"/usr/bin/{name}" if name in {"wezterm", "ghostty"} else None

    monkeypatch.setattr(terminal_launchers.shutil, "which", which)
    monkeypatch.setattr(terminal_launchers.os, "environ", {"WEZTERM_PANE": "1"})
    monkeypatch.setattr(
        terminal_launchers.subprocess,
        "Popen",
        lambda command, **kwargs: launches.append((command, kwargs)) or object(),
    )

    plan = terminal_launchers.launch_codex_bridge(
        socket_path="/tmp/lwa.sock",
        cwd="/tmp",
        codex="codex-test",
        disable_lwa_mcp=False,
    )
    assert plan.launcher == "wezterm-split"
    assert plan.mode == "split"
    assert launches[0][0][0] == "/usr/bin/wezterm"


def test_terminal_adapter_override_covers_all_named_window_hosts(monkeypatch):
    from lwa_mcp import terminal_launchers

    for terminal in ("ghostty", "alacritty", "tabby", "wave", "gnome-terminal", "konsole", "terminator", "guake"):
        launches = []

        def record_launch(command, _launches=launches, **kwargs):
            _launches.append((command, kwargs))
            return object()

        monkeypatch.setenv("LWA_TERMINAL_ADAPTER", terminal)
        monkeypatch.setattr(terminal_launchers.shutil, "which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(
            terminal_launchers.subprocess,
            "Popen",
            record_launch,
        )
        plan = terminal_launchers.launch_codex_bridge(
            socket_path="/tmp/lwa.sock",
            cwd="/tmp/project with spaces",
            codex="codex-test",
            disable_lwa_mcp=True,
        )
        assert plan.capabilities is not None
        assert plan.capabilities.terminal == terminal
        assert plan.mode == "window"
        assert launches[0][0][0] == f"/usr/bin/{terminal}"
        assert "/tmp/project with spaces" in launches[0][0]


def test_kitty_remote_control_uses_same_session_split(monkeypatch):
    from lwa_mcp import terminal_launchers

    launches = []
    monkeypatch.setenv("LWA_TERMINAL_ADAPTER", "kitty")
    monkeypatch.setenv("KITTY_LISTEN_ON", "unix:/tmp/kitty.sock")
    monkeypatch.setattr(terminal_launchers.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        terminal_launchers.subprocess,
        "Popen",
        lambda command, **kwargs: launches.append((command, kwargs)) or object(),
    )
    plan = terminal_launchers.launch_codex_bridge(
        socket_path="/tmp/lwa.sock",
        cwd="/tmp/project",
        codex="codex-test",
        disable_lwa_mcp=False,
    )
    assert plan.launcher == "kitty-split"
    assert plan.mode == "split"
    assert launches[0][0][1:4] == ["@", "launch", "--location=vsplit"]


def test_additional_terminal_adapters_are_classified(monkeypatch):
    from lwa_mcp import terminal_launchers

    for terminal in (
        "lxterminal",
        "cool-retro-term",
        "terminus",
        "rio",
        "blackbox",
        "ptyxis",
        "yakuake",
        "sakura",
        "lilyterm",
        "xfce4-terminal",
        "ratty",
        "tilda",
    ):
        launches = []

        def record_launch(command, _launches=launches, **kwargs):
            _launches.append((command, kwargs))
            return object()

        monkeypatch.setenv("LWA_TERMINAL_ADAPTER", terminal)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.setattr(terminal_launchers.shutil, "which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(terminal_launchers.subprocess, "Popen", record_launch)
        plan = terminal_launchers.launch_codex_bridge(
            socket_path="/tmp/lwa.sock",
            cwd="/tmp/project with spaces",
            codex="codex-test",
            disable_lwa_mcp=True,
        )
        assert plan.capabilities is not None
        assert plan.capabilities.terminal == terminal
        assert plan.mode == "window"
        assert launches


def test_tmux_uses_split_only_inside_tmux(monkeypatch):
    from lwa_mcp import terminal_launchers

    launches = []
    monkeypatch.setenv("LWA_TERMINAL_ADAPTER", "tmux")
    monkeypatch.setenv("TMUX", "/tmp/tmux,1,0")
    monkeypatch.setenv("TMUX_PANE", "%0")
    monkeypatch.setattr(terminal_launchers.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        terminal_launchers.subprocess,
        "Popen",
        lambda command, **kwargs: launches.append((command, kwargs)) or object(),
    )
    plan = terminal_launchers.launch_codex_bridge(
        socket_path="/tmp/lwa.sock",
        cwd="/tmp/project",
        codex="codex-test",
        disable_lwa_mcp=False,
    )
    assert plan.launcher == "tmux-split"
    assert plan.mode == "split"
    assert launches[0][0][1:5] == ["split-window", "-h", "-t", "%0"]


def test_unknown_terminal_override_fails_closed(monkeypatch):
    from lwa_mcp import terminal_launchers

    monkeypatch.setenv("LWA_TERMINAL_ADAPTER", "not-a-terminal")
    try:
        terminal_launchers.launch_codex_bridge(
            socket_path="/tmp/lwa.sock",
            cwd="/tmp",
            codex="codex-test",
            disable_lwa_mcp=True,
        )
    except RuntimeError as exc:
        assert "Unknown LWA_TERMINAL_ADAPTER" in str(exc)
    else:  # pragma: no cover - assertion branch
        raise AssertionError("unknown adapter must fail closed")


def test_launch_frame_cleans_socket_when_controller_fails(monkeypatch, tmp_path):
    from lwa_mcp import launch

    class FakeProcess:
        def __init__(self):
            self.terminated = False

        def poll(self):
            return None if not self.terminated else 0

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            return 0

        def kill(self):
            self.terminated = True

    process = FakeProcess()
    socket_path = tmp_path / "lwa-mcp" / "codex-bridge-bridge-token.sock"

    def fake_launch(**kwargs):
        socket_path.parent.mkdir(exist_ok=True)
        socket_path.touch()
        return SimpleNamespace(process=process)

    monkeypatch.setattr(launch, "_codex_executable", lambda: "codex-test")
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    monkeypatch.delenv("GHOSTTY_RESOURCES_DIR", raising=False)
    monkeypatch.setattr(launch, "launch_codex_bridge", fake_launch)
    monkeypatch.setattr(launch.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(launch.secrets, "token_hex", lambda _size: "bridge-token")
    monkeypatch.setattr(
        "lwa_mcp.terminal_frame.run",
        lambda executable, *, bridge_socket=None: (_ for _ in ()).throw(RuntimeError("attach failed")),
    )

    args = type("Args", (), {"codex": None, "fallback": False})()
    assert launch.launch_frame(args) == 1
    assert not socket_path.exists()
    assert process.terminated is True


def test_ghostty_bootstrap_enters_tmux_for_same_window_split(monkeypatch):
    from lwa_mcp import launch

    calls = []
    monkeypatch.setenv("TERM_PROGRAM", "ghostty")
    monkeypatch.delenv("TMUX", raising=False)
    monkeypatch.delenv("LWA_TMUX_BOOTSTRAPPED", raising=False)
    monkeypatch.setattr(launch.shutil, "which", lambda name: "/usr/bin/tmux" if name == "tmux" else None)
    monkeypatch.setattr(
        launch.subprocess,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)) or SimpleNamespace(returncode=0),
    )

    args = SimpleNamespace(codex="codex-test")
    assert launch._maybe_bootstrap_ghostty_split(args) == 0
    assert calls[0][0][0] == "/usr/bin/tmux"
    assert calls[0][0][1:6] == ["new-session", "-A", "-s", calls[0][0][4], "-c"]
    assert calls[0][1]["env"]["LWA_TMUX_BOOTSTRAPPED"] == "1"
    assert "TMUX" not in calls[0][1]["env"]
    assert "TMUX_PANE" not in calls[0][1]["env"]


def test_native_tmux_split_returns_direct_codex_pane(monkeypatch, capsys):
    from lwa_mcp import launch

    monkeypatch.setenv("TMUX", "/tmp/tmux,1,0")
    monkeypatch.setenv("TMUX_PANE", "%0")
    monkeypatch.setattr(launch.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        launch.subprocess,
        "run",
        lambda command, **kwargs: type("Result", (), {"returncode": 0, "stdout": "%7\n", "stderr": ""})(),
    )

    assert launch._native_tmux_split_enabled() is True
    assert launch._launch_native_tmux_codex(codex="/usr/bin/codex", cwd="/tmp/project") == "%7"
    assert capsys.readouterr().out == ""


def test_native_focus_bindings_use_exact_panes_and_source_aware_keys(monkeypatch):
    from lwa_mcp import launch

    calls = []
    monkeypatch.setattr(
        launch.subprocess,
        "run",
        lambda command, **kwargs: calls.append(command),
    )

    launch._install_native_focus_bindings(tmux="tmux-test", lwa_pane="%1", codex_pane="%2")

    assert [command[4] for command in calls[-2:]] == ["M-Left", "M-Right"]
    assert "select-pane -t %1" in " ".join(calls[-2])
    assert "select-pane -t %2" in " ".join(calls[-1])
    assert all("send-keys" not in " ".join(command) for command in calls)
    assert [command[-1] for command in calls[:5]] == ["M-Left", "M-Right", "Tab", "BTab", "C-i"]


def test_native_c_copy_binding_is_scoped_to_codex(monkeypatch):
    from lwa_mcp import launch

    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[1] == "split-window":
            return SimpleNamespace(returncode=0, stdout="%2\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(launch.shutil, "which", lambda name: "/usr/bin/tmux" if name == "tmux" else None)
    monkeypatch.setattr(launch.subprocess, "run", fake_run)
    monkeypatch.setenv("TMUX_PANE", "%1")

    launch._launch_native_tmux_codex(codex="/usr/bin/codex", cwd="/tmp/project")

    c_copy = next(command for command in calls if command[-2:] == ["C-c", "if-shell"] or "C-c" in command)
    assert "if-shell" in c_copy
    assert "%2" in " ".join(c_copy) and "%1" in " ".join(c_copy)


def test_native_tmux_split_keeps_lwa_module_enabled_by_default(monkeypatch):
    from lwa_mcp import launch

    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[1] == "split-window":
            return SimpleNamespace(returncode=0, stdout="%7\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(launch.shutil, "which", lambda name: "/usr/bin/tmux" if name == "tmux" else None)
    monkeypatch.setattr(launch.subprocess, "run", fake_run)
    monkeypatch.delenv("LWA_NATIVE_DISABLE_MCP", raising=False)

    launch._launch_native_tmux_codex(codex="/usr/bin/codex", cwd="/tmp/project")

    split_command = calls[0]
    assert 'plugins."lwa-mcp@armando-local".enabled=false' not in split_command


def test_native_tmux_split_can_disable_lwa_module_explicitly(monkeypatch):
    from lwa_mcp import launch

    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[1] == "split-window":
            return SimpleNamespace(returncode=0, stdout="%7\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(launch.shutil, "which", lambda name: "/usr/bin/tmux" if name == "tmux" else None)
    monkeypatch.setattr(launch.subprocess, "run", fake_run)
    monkeypatch.setenv("LWA_NATIVE_DISABLE_MCP", "1")

    launch._launch_native_tmux_codex(codex="/usr/bin/codex", cwd="/tmp/project")

    split_command = next(command for command in calls if "split-window" in command)
    assert 'plugins."lwa-mcp@armando-local".enabled=false' in split_command


def test_native_tmux_split_can_be_disabled(monkeypatch):
    from lwa_mcp import launch

    monkeypatch.setenv("TMUX", "/tmp/tmux,1,0")
    monkeypatch.setenv("LWA_NATIVE_SPLIT", "window")
    assert launch._native_tmux_split_enabled() is False
