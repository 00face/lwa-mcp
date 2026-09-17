from __future__ import annotations

from lwa_mcp.resource_budget import BoundedLines, budget_float, budget_int, redraw_due


def test_bounded_lines_trims_append_and_extend():
    lines = BoundedLines([str(index) for index in range(19)], max_lines=20)
    lines.append("19")
    lines.extend(["20", "21"])
    assert lines == [str(index) for index in range(2, 22)]


def test_budget_int_is_clamped_and_resists_invalid_values(monkeypatch):
    monkeypatch.setenv("LWA_TEST_BUDGET", "999999")
    assert budget_int("LWA_TEST_BUDGET", 10, minimum=2, maximum=100) == 100
    monkeypatch.setenv("LWA_TEST_BUDGET", "bad")
    assert budget_int("LWA_TEST_BUDGET", 10, minimum=2, maximum=100) == 10


def test_budget_float_is_clamped_and_redraw_signature_is_change_sensitive(monkeypatch):
    monkeypatch.setenv("LWA_TEST_INTERVAL", "0.001")
    assert budget_float("LWA_TEST_INTERVAL", 0.04, minimum=0.02, maximum=0.25) == 0.02
    assert redraw_due((1,), (2,), 10_000, minimum_interval=10) is True
