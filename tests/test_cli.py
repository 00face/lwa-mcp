from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


def test_ensure_dashboard_running_starts_dashboard_when_needed(monkeypatch):
    from lwa_mcp import cli

    calls = []
    states = iter([False, False, True])

    def fake_running(host, port):
        return next(states)

    monkeypatch.setattr(cli.RouterService, "_dashboard_running", fake_running)
    monkeypatch.setattr(cli, "_dashboard_executable", lambda: Path("/tmp/lwa-dashboard"))
    monkeypatch.setattr(
        cli.subprocess,
        "Popen",
        lambda *args, **kwargs: calls.append((args, kwargs)) or SimpleNamespace(),
    )
    monkeypatch.setattr(cli.time, "sleep", lambda *_: None)

    svc = SimpleNamespace(
        config=SimpleNamespace(
            settings=SimpleNamespace(dashboard_host="127.0.0.1", dashboard_port=8766)
        )
    )

    started, url = cli._ensure_dashboard_running(svc)

    assert started is True
    assert url == "http://127.0.0.1:8766"
    assert calls[0][0][0] == ["/tmp/lwa-dashboard"]


def test_ensure_dashboard_running_noops_when_dashboard_is_already_up(monkeypatch):
    from lwa_mcp import cli

    monkeypatch.setattr(cli.RouterService, "_dashboard_running", lambda host, port: True)
    monkeypatch.setattr(
        cli.subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail("Popen should not be called when the dashboard is up"),
    )

    svc = SimpleNamespace(
        config=SimpleNamespace(
            settings=SimpleNamespace(dashboard_host="127.0.0.1", dashboard_port=8766)
        )
    )

    started, url = cli._ensure_dashboard_running(svc)

    assert started is False
    assert url == "http://127.0.0.1:8766"


@pytest.mark.asyncio
async def test_doctor_can_surface_dashboard_url(monkeypatch, capsys):
    from lwa_mcp import cli

    class FakeCatalog:
        async def refresh(self, force: bool = False):
            return {"models": 1, "refreshed": 1}

    class FakeLibrary:
        def summary(self):
            return {"root": "/tmp/tool-library", "active": 1, "draft": 0, "generated": 0}

    class FakeDB:
        def list_workflow_patterns(self, limit: int):
            return []

    class FakeService:
        def __init__(self, config=None):
            self.config = SimpleNamespace(
                settings=SimpleNamespace(dashboard_host="127.0.0.1", dashboard_port=8766)
            )
            self.catalog = FakeCatalog()
            self.library = FakeLibrary()
            self.db = FakeDB()

        async def initialize(self) -> None:
            return None

        def providers_json(self):
            return [
                {
                    "enabled": True,
                    "experimental": False,
                    "configured": True,
                    "name": "mock",
                    "adapter": "openai",
                    "billing_class": "free_quota",
                    "disabled_reason": None,
                }
            ]

    monkeypatch.setattr(cli, "RouterService", FakeService)
    monkeypatch.setattr(cli, "load_config", lambda: None)
    monkeypatch.setattr(cli, "_ensure_dashboard_running", lambda svc: (True, "http://127.0.0.1:8766"))

    assert await cli.doctor(True) == 0

    output = capsys.readouterr().out
    assert "Dashboard URL: http://127.0.0.1:8766 (started)" in output
