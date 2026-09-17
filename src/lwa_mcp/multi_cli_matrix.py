"""Local concurrent proof for the supported multi-CLI command boundary."""

from __future__ import annotations

import importlib.util
import threading
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any

from .command_prefix import parse_command
from .task_ledger import TaskLedger
from .task_ledger import LedgerConflict
from .write_ownership import OwnershipConflict, OwnershipRegistry


def _broker():
    path = Path(__file__).resolve().parents[2] / "scripts/lwa-cli-broker"
    spec = importlib.util.spec_from_loader("lwa_matrix_broker", SourceFileLoader("lwa_matrix_broker", str(path)))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def run_matrix(root: Path) -> dict[str, Any]:
    ledger = TaskLedger(root / "ledger.sqlite3")
    broker = _broker()
    broker.register_command("matrix", ["/bin/printf"])
    commands = [("!e", "codex"), ("!$", "agy"), ("!d", "gemini"), ("!c", "vibe")]
    entries: list[dict[str, Any]] = []
    errors: list[str] = []

    def invoke(index: int, pair: tuple[str, str]) -> None:
        prefix, actor = pair
        task_id = f"matrix-{index}"
        ledger.create_task(task_id, prefix, owner=actor)
        ledger.claim(task_id, actor, lease_seconds=30)
        parsed = parse_command(f"{prefix} fixture")
        try:
            result = broker.execute("matrix", [parsed.mode], ledger=ledger, task_id=task_id, actor=actor, output_limit=32)
            entries.append({"prefix": prefix, "actor": actor, "mode": parsed.mode,
                            "lease_attributed": result["task_id"] == task_id,
                            "bounded": result["output_truncated"] is False})
        except Exception as exc:  # pragma: no cover - surfaced in result
            errors.append(f"{prefix}:{type(exc).__name__}")

    threads = [threading.Thread(target=invoke, args=(i, pair)) for i, pair in enumerate(commands)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    ledger.create_task("bypass", "direct", owner="codex")
    ledger.claim("bypass", "codex", lease_seconds=30)
    try:
        broker.execute("/bin/echo", ["bypass"], ledger=ledger, task_id="bypass", actor="codex")
    except broker.BrokerError:
        direct_bypass = "blocked"
    else:
        direct_bypass = "unsafe"
    expiry = OwnershipRegistry(root / "expiry.json")
    expiry.grant("expired", "codex", ["docs/**"], expires_at="2000-01-01T00:00:00+00:00")
    try:
        expiry.authorize("expired", "codex", "docs/a.md")
    except OwnershipConflict:
        lease_expiry = "blocked"
    else:
        lease_expiry = "unsafe"
    revoke = OwnershipRegistry(root / "revoke.json")
    revoke.grant("revoked", "codex", ["src/**"])
    revoke.delegate("revoked", "codex", "agy", ["src/lib/**"])
    revoke.revoke("revoked", "agy", actor="codex")
    try:
        revoke.authorize("revoked", "agy", "src/lib/a.py")
    except OwnershipConflict:
        revocation = "blocked"
    else:
        revocation = "unsafe"
    ledger.stop("bypass", "fixture cancellation", actor="codex")
    try:
        ledger.transition("bypass", "running", actor="codex")
    except LedgerConflict:
        cancellation = "blocked"
    else:
        cancellation = "unsafe"
    status = "passed" if len(entries) == 4 and not errors and direct_bypass == "blocked" and lease_expiry == "blocked" and revocation == "blocked" and cancellation == "blocked" else "blocked"
    return {"schema": "lwa-multi-cli-matrix/v1", "status": status, "entries": sorted(entries, key=lambda item: item["prefix"]), "direct_bypass": direct_bypass, "lease_expiry": lease_expiry, "revocation": revocation, "cancellation": cancellation}
