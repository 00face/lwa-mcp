from __future__ import annotations

import sqlite3

from lwa_mcp.db import UsageDB
from lwa_mcp.models import (
    BillingClass,
    CompletionResult,
    ModelCandidate,
    RouteDecision,
    RouteRequest,
    TaskKind,
)
from lwa_mcp.telemetry import validate_telemetry_export


def test_usage_db_initialization_recovers_from_unopenable_database(tmp_path, monkeypatch):
    calls: list[str] = []
    attempts: list[int] = []

    class FakeConnection:
        def __init__(self) -> None:
            self.row_factory = None

        def executescript(self, script: str):
            calls.append(script)
            attempts.append(1)
            if len(attempts) == 1:
                raise sqlite3.OperationalError("unable to open database file")
            return self

        def commit(self) -> None:
            return None

        def close(self) -> None:
            return None

    monkeypatch.setattr("lwa_mcp.db.sqlite3.connect", lambda path: FakeConnection())

    db_path = tmp_path / "state" / "lwa.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_bytes(b"broken")

    UsageDB(db_path)

    assert any("CREATE TABLE IF NOT EXISTS requests" in call for call in calls)
    backups = list(db_path.parent.glob("lwa.sqlite3.corrupt-*"))
    assert backups
    assert not db_path.exists()


def test_usage_db_records_attribution_and_unreported_usage_without_prompt_body(tmp_path):
    db = UsageDB(tmp_path / "state" / "lwa.sqlite3")
    request = RouteRequest(
        task=TaskKind.QUERY,
        prompt="do not persist this prompt body",
        metadata={
            "session_id": "session-1",
            "call_id": "call-1",
            "tool_name": "answer_query",
            "cache_hit": True,
            "redundant_call": False,
            "secret": "must-not-be-stored",
        },
    )
    decision = RouteDecision(
        candidate=ModelCandidate(
            provider="mock",
            model="mock-model",
            billing_class=BillingClass.FREE,
        ),
        score=1,
        reasons=["test"],
        estimated_input_tokens=4,
    )

    db.record_result(
        request,
        decision,
        CompletionResult(
            provider="mock",
            model="mock-model",
            text="ok",
            input_tokens=3,
            output_tokens=2,
            raw_usage={"total_tokens": 5},
            usage_reported=True,
        ),
        "ok",
    )
    db.record_result(request, decision, None, "error", {"error": "redacted"})

    summary = db.dashboard_summary()
    assert summary["telemetry"] == {
        "total_calls": 2,
        "reported_calls": 1,
        "unreported_calls": 1,
        "total_tokens": 9,
        "reported_tokens": 5,
        "cache_hits": 2,
        "redundant_calls": 0,
        "unattributed_calls": 0,
    }
    assert summary["telemetry_health"] == {
        "usage_reporting_complete": False,
        "attribution_complete": True,
        "unreported_calls": 1,
        "unattributed_calls": 0,
        "ten_of_ten_ready": False,
    }
    assert "do not persist this prompt body" not in repr(summary)
    assert "must-not-be-stored" not in repr(summary)
    assert summary["recent"][0]["session_id"] == "session-1"
    assert summary["recent"][0]["parent_call_id"] == "call-1"
    assert summary["recent"][0]["tool_name"] == "answer_query"
    exported = db.export_telemetry()
    assert exported["redacted"] is True
    assert exported["records"][0]["call_id"] == "call-1"
    assert validate_telemetry_export(exported)["valid"] is True


def test_telemetry_export_rejects_missing_attribution_and_sensitive_fields():
    record = {
        "id": 1,
        "created_at": "2026-08-08T00:00:00Z",
        "task": "query",
        "provider": "mock",
        "model": "mock-model",
        "billing_class": "free",
        "input_tokens": 1,
        "output_tokens": 1,
        "latency_ms": 1,
        "status": "ok",
        "prompt_hash": "hash",
        "session_id": None,
        "call_id": "call",
        "parent_call_id": "call",
        "tool_name": "query",
        "phase": "provider_execution",
        "cache_hit": 0,
        "redundant_call": 0,
        "usage_status": "reported",
        "prompt": "must not be exported",
    }
    result = validate_telemetry_export({"schema_version": 1, "redacted": True, "records": [record]})
    assert result["valid"] is False
    assert any("sensitive" in error for error in result["errors"])
    assert any("missing_attribution:session_id" in error for error in result["errors"])
