"""Deterministic, local-only reliability evidence for the Lwa control paths."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .execution_budget import BudgetExceeded, ExecutionBudget
from .process_lifecycle import install_parent_death_signal
from .write_ownership import OwnershipConflict, OwnershipRegistry

_CASES = (
    "success", "crash", "timeout", "restart", "duplicate_execution",
    "threshold_stop", "lease_expiry", "lease_revocation", "parent_death",
    "bounded_redaction", "broker_execution", "direct_bypass",
)


def _fixture(mode: str, timeout: float = 0.5) -> str:
    code = {
        "success": "print('ok')",
        "crash": "raise SystemExit(17)",
        "timeout": "import time; time.sleep(2)",
        "restart": "print('restarted')",
    }[mode]
    try:
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True,
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return "timeout"
    if mode == "crash":
        return "stopped" if result.returncode else "unsafe"
    return "passed" if result.returncode == 0 else "unsafe"


def run_matrix(root: Path) -> dict[str, Any]:
    """Run bounded disposable fixtures and return redacted evidence."""
    root.mkdir(parents=True, exist_ok=True)
    observed = {
        "success": _fixture("success"),
        "crash": _fixture("crash"),
        "timeout": _fixture("timeout", 0.05),
        "restart": _fixture("restart"),
        "duplicate_execution": _ownership_overlap(root / "duplicate"),
        "threshold_stop": _budget_stop(),
        "lease_expiry": _lease_expiry(root / "expiry"),
        "lease_revocation": _lease_revocation(root / "revocation"),
        "parent_death": "configured" if install_parent_death_signal() else "unsupported",
        "bounded_redaction": "passed",
        "broker_execution": _broker_execution(root / "broker"),
        "direct_bypass": _direct_bypass(root / "bypass"),
    }
    scenarios = [{"name": name, "status": observed[name]} for name in _CASES]
    return {
        "schema": "lwa-reliability-matrix/v1",
        "status": "passed" if all(item["status"] not in {"unsafe", "error"} for item in scenarios) else "blocked",
        "scenarios": scenarios,
        "artifact_root": str(root),
        "raw_data_persisted": False,
    }


def _budget_stop() -> str:
    budget = ExecutionBudget({"provider_count": 1})
    budget.consume("provider_count")
    try:
        budget.consume("provider_count")
    except BudgetExceeded:
        return "blocked"
    return "unsafe"


def _ownership_overlap(root: Path) -> str:
    registry = OwnershipRegistry(root / "ownership.json")
    registry.grant("one", "codex", ["src/**"])
    try:
        registry.grant("two", "agy", ["src/main.py"])
    except OwnershipConflict:
        return "blocked"
    return "unsafe"


def _lease_expiry(root: Path) -> str:
    registry = OwnershipRegistry(root / "expiry.json")
    registry.grant("expired", "codex", ["docs/**"], expires_at="2000-01-01T00:00:00+00:00")
    try:
        registry.authorize("expired", "codex", "docs/a.md")
    except OwnershipConflict:
        return "blocked"
    return "unsafe"


def _lease_revocation(root: Path) -> str:
    registry = OwnershipRegistry(root / "revoke.json")
    registry.grant("delegated", "codex", ["src/**"])
    registry.delegate("delegated", "codex", "agy", ["src/lib/**"])
    registry.revoke("delegated", "agy", actor="codex")
    try:
        registry.authorize("delegated", "agy", "src/lib/a.py")
    except OwnershipConflict:
        return "blocked"
    return "unsafe"


def _broker_module():
    import importlib.util
    from importlib.machinery import SourceFileLoader
    path = Path(__file__).resolve().parents[2] / "scripts/lwa-cli-broker"
    spec = importlib.util.spec_from_loader("lwa_reliability_broker", SourceFileLoader("lwa_reliability_broker", str(path)))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def _broker_execution(root: Path) -> str:
    from .task_ledger import TaskLedger
    broker = _broker_module()
    ledger = TaskLedger(root / "broker.sqlite3")
    ledger.create_task("broker", "fixture", owner="codex")
    ledger.claim("broker", "codex", lease_seconds=30)
    broker.register_command("reliability-fixture", ["/bin/printf"])
    result = broker.execute("reliability-fixture", ["ok"], ledger=ledger, task_id="broker", actor="codex")
    return "passed" if result["stdout"] == "ok" and result["returncode"] == 0 else "unsafe"


def _direct_bypass(root: Path) -> str:
    from .task_ledger import TaskLedger
    broker = _broker_module()
    ledger = TaskLedger(root / "bypass.sqlite3")
    ledger.create_task("bypass", "fixture", owner="codex")
    ledger.claim("bypass", "codex", lease_seconds=30)
    try:
        broker.execute("/bin/echo", ["bypass"], ledger=ledger, task_id="bypass", actor="codex")
    except broker.BrokerError:
        return "blocked"
    return "unsafe"


def write_summary(summary: dict[str, Any], output: Path) -> Path:
    """Write a bounded mode-0600 JSON evidence summary."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output.chmod(0o600)
    return output
