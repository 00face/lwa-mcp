from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import CompletionResult, PreflightSummary, RouteDecision, RouteRequest


class UsageDB:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _init(self, *, allow_recovery: bool = True) -> None:
        try:
            with self.connect() as con:
                con.executescript(
                    """
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    task TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    billing_class TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL DEFAULT 0,
                    output_tokens INTEGER NOT NULL DEFAULT 0,
                    cost_usd REAL,
                    latency_ms INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    prompt_hash TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    session_id TEXT,
                    call_id TEXT,
                    parent_call_id TEXT,
                    tool_name TEXT,
                    phase TEXT,
                    cache_hit INTEGER NOT NULL DEFAULT 0,
                    redundant_call INTEGER NOT NULL DEFAULT 0,
                    usage_status TEXT NOT NULL DEFAULT 'not_reported'
                );
                CREATE TABLE IF NOT EXISTS route_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    task TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    score REAL NOT NULL,
                    reasons_json TEXT NOT NULL,
                    requires_confirmation INTEGER NOT NULL DEFAULT 0,
                    session_id TEXT,
                    call_id TEXT,
                    parent_call_id TEXT,
                    tool_name TEXT,
                    phase TEXT
                );
                CREATE TABLE IF NOT EXISTS preflight_events (
                    plan_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    task TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    working_may_begin INTEGER NOT NULL DEFAULT 0,
                    requires_confirmation INTEGER NOT NULL DEFAULT 0,
                    prompt_hash TEXT NOT NULL,
                    estimated_input_tokens INTEGER NOT NULL DEFAULT 0,
                    max_output_tokens INTEGER NOT NULL DEFAULT 0,
                    routes_json TEXT NOT NULL DEFAULT '[]',
                    locks_json TEXT NOT NULL DEFAULT '{}',
                    working_started_at TEXT,
                    completed_at TEXT,
                    session_id TEXT,
                    call_id TEXT,
                    parent_call_id TEXT,
                    tool_name TEXT
                );
                CREATE TABLE IF NOT EXISTS quota_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    values_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS workflow_patterns (
                    signature TEXT PRIMARY KEY,
                    task TEXT NOT NULL,
                    label TEXT NOT NULL,
                    description TEXT NOT NULL,
                    keywords_json TEXT NOT NULL DEFAULT '[]',
                    occurrences INTEGER NOT NULL DEFAULT 0,
                    successes INTEGER NOT NULL DEFAULT 0,
                    confidence REAL NOT NULL DEFAULT 0,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    tool_slug TEXT,
                    project TEXT
                );
                CREATE TABLE IF NOT EXISTS workflow_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    task TEXT NOT NULL,
                    success INTEGER NOT NULL DEFAULT 1,
                    project TEXT,
                    prompt_hash TEXT
                );
                    """
                )
                self._ensure_columns(con)
        except sqlite3.OperationalError as exc:
            if allow_recovery and self._should_recover(exc):
                self._quarantine_existing_database()
                self._init(allow_recovery=False)
                return
            raise

    @staticmethod
    def _ensure_columns(con: sqlite3.Connection) -> None:
        if not hasattr(con, "execute"):
            return
        migrations = {
            "requests": {
                "session_id": "TEXT",
                "call_id": "TEXT",
                "parent_call_id": "TEXT",
                "tool_name": "TEXT",
                "phase": "TEXT",
                "cache_hit": "INTEGER NOT NULL DEFAULT 0",
                "redundant_call": "INTEGER NOT NULL DEFAULT 0",
                "usage_status": "TEXT NOT NULL DEFAULT 'not_reported'",
            },
            "route_events": {
                "session_id": "TEXT",
                "call_id": "TEXT",
                "parent_call_id": "TEXT",
                "tool_name": "TEXT",
                "phase": "TEXT",
            },
            "preflight_events": {
                "session_id": "TEXT",
                "call_id": "TEXT",
                "parent_call_id": "TEXT",
                "tool_name": "TEXT",
            },
        }
        for table, columns in migrations.items():
            existing = {row[1] for row in con.execute(f"PRAGMA table_info({table})")}
            for name, definition in columns.items():
                if name not in existing:
                    con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    @staticmethod
    def _telemetry_fields(
        request: RouteRequest, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        allowed = {
            "session_id", "parent_call_id", "call_id", "tool_name", "phase",
            "cache_hit", "redundant_call", "reasoning_effort",
        }
        fields = {key: value for key, value in request.metadata.items() if key in allowed}
        fields.update({key: value for key, value in (metadata or {}).items() if key in allowed})
        fields.setdefault("session_id", None)
        fields.setdefault("call_id", None)
        fields.setdefault("parent_call_id", fields.get("call_id"))
        fields.setdefault("tool_name", "router_service")
        fields.setdefault("phase", "provider_execution")
        fields["cache_hit"] = int(bool(fields.get("cache_hit", False)))
        fields["redundant_call"] = int(bool(fields.get("redundant_call", False)))
        return fields

    def _should_recover(self, exc: sqlite3.OperationalError) -> bool:
        return "unable to open database file" in str(exc).lower()

    def _quarantine_existing_database(self) -> None:
        if not self.path.exists():
            return
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        backup = self.path.with_name(f"{self.path.name}.corrupt-{stamp}")
        try:
            self.path.replace(backup)
        except OSError:
            return
        for suffix in ("-wal", "-shm"):
            sidecar = Path(f"{self.path}{suffix}")
            if sidecar.exists():
                try:
                    sidecar.unlink()
                except OSError:
                    pass


    def record_preflight(self, summary: PreflightSummary) -> None:
        now = datetime.now(UTC).isoformat()
        routes = [
            {
                "role": route.role,
                "order": route.order,
                "provider": route.decision.candidate.provider,
                "model": route.decision.candidate.model,
                "billing_class": route.decision.candidate.billing_class.value,
            }
            for route in summary.routes
        ]
        with self.connect() as con:
            con.execute(
                """INSERT INTO preflight_events
                (plan_id, created_at, updated_at, task, mode, status, working_may_begin,
                 requires_confirmation, prompt_hash, estimated_input_tokens, max_output_tokens,
                 routes_json, locks_json, session_id, call_id, parent_call_id, tool_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(plan_id) DO UPDATE SET
                    updated_at=excluded.updated_at, status=excluded.status,
                    working_may_begin=excluded.working_may_begin,
                    routes_json=excluded.routes_json, locks_json=excluded.locks_json""",
                (
                    summary.plan_id, summary.created_at.isoformat(), now, summary.task.value,
                    summary.mode, summary.status, int(summary.working_may_begin),
                    int(summary.requires_confirmation), summary.prompt_hash,
                    summary.estimated_input_tokens, summary.max_output_tokens,
                    json.dumps(routes), json.dumps(summary.locks), summary.session_id,
                    summary.call_id, summary.parent_call_id, summary.tool_name,
                ),
            )

    def update_preflight_status(
        self, plan_id: str, status: str, *, working_may_begin: bool | None = None
    ) -> None:
        now = datetime.now(UTC).isoformat()
        columns = ["status=?", "updated_at=?"]
        values: list[Any] = [status, now]
        if working_may_begin is not None:
            columns.append("working_may_begin=?")
            values.append(int(working_may_begin))
        if status == "working":
            columns.append("working_started_at=?")
            values.append(now)
        if status in {"completed", "failed", "repreflight_required"}:
            columns.append("completed_at=?")
            values.append(now)
        values.append(plan_id)
        with self.connect() as con:
            con.execute(
                f"UPDATE preflight_events SET {', '.join(columns)} WHERE plan_id=?", values
            )

    def record_route(self, request: RouteRequest, decision: RouteDecision) -> None:
        fields = self._telemetry_fields(request, {"phase": "route"})
        with self.connect() as con:
            con.execute(
                """INSERT INTO route_events
                (created_at, task, provider, model, score, reasons_json, requires_confirmation,
                 session_id, call_id, parent_call_id, tool_name, phase)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now(UTC).isoformat(),
                    request.task.value,
                    decision.candidate.provider,
                    decision.candidate.model,
                    decision.score,
                    json.dumps(decision.reasons),
                    int(decision.requires_confirmation),
                    fields["session_id"], fields["call_id"], fields["parent_call_id"], fields["tool_name"],
                    fields["phase"],
                ),
            )

    def record_result(
        self,
        request: RouteRequest,
        decision: RouteDecision,
        result: CompletionResult | None,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        import hashlib
        fields = self._telemetry_fields(request, metadata)
        usage_status = (
            "reported"
            if result and result.usage_reported
            else "not_reported"
        )
        stored_metadata = {
            key: value for key, value in (metadata or {}).items() if key in {"error"}
        }
        stored_metadata["usage_status"] = usage_status
        if request.reasoning_effort is not None:
            stored_metadata["reasoning_effort"] = getattr(
                request.reasoning_effort, "value", str(request.reasoning_effort)
            )
        if result:
            stored_metadata.update(
                {
                    "result_provider": result.provider,
                    "result_model": result.model,
                    "transport": result.transport,
                    "response_id": result.response_id,
                    "usage_reported": result.usage_reported,
                }
            )

        with self.connect() as con:
            con.execute(
                """INSERT INTO requests
                (created_at, task, provider, model, billing_class, input_tokens,
                 output_tokens, cost_usd, latency_ms, status, prompt_hash, metadata_json,
                 session_id, call_id, parent_call_id, tool_name, phase, cache_hit, redundant_call,
                 usage_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now(UTC).isoformat(),
                    request.task.value,
                    decision.candidate.provider,
                    decision.candidate.model,
                    decision.candidate.billing_class.value,
                    result.input_tokens if result else decision.estimated_input_tokens,
                    result.output_tokens if result else 0,
                    result.cost_usd if result else None,
                    result.latency_ms if result else 0,
                    status,
                    hashlib.sha256(request.prompt.encode("utf-8")).hexdigest(),
                    json.dumps(stored_metadata),
                    fields["session_id"], fields["call_id"], fields["parent_call_id"], fields["tool_name"],
                    fields["phase"], fields["cache_hit"], fields["redundant_call"],
                    usage_status,
                ),
            )
            if result and result.rate_limits:
                con.execute(
                    "INSERT INTO quota_snapshots (created_at, provider, values_json) VALUES (?, ?, ?)",
                    (
                        datetime.now(UTC).isoformat(),
                        result.provider,
                        json.dumps(result.rate_limits),
                    ),
                )

    def record_quota_snapshot(self, provider: str, values: dict[str, Any]) -> None:
        with self.connect() as con:
            con.execute(
                "INSERT INTO quota_snapshots (created_at, provider, values_json) VALUES (?, ?, ?)",
                (datetime.now(UTC).isoformat(), provider, json.dumps(values)),
            )

    def set_setting(self, key: str, value: str) -> None:
        with self.connect() as con:
            con.execute(
                """INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (key, value, datetime.now(UTC).isoformat()),
            )

    def get_setting(self, key: str) -> str | None:
        with self.connect() as con:
            row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return str(row["value"]) if row else None


    def upsert_workflow_pattern(
        self,
        *,
        signature: str,
        task: str,
        label: str,
        description: str,
        keywords: list[str],
        success: bool,
        confidence: float,
        project: str | None = None,
        prompt_hash: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        with self.connect() as con:
            con.execute(
                """INSERT INTO workflow_patterns
                (signature, task, label, description, keywords_json, occurrences, successes,
                 confidence, first_seen, last_seen, project)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
                ON CONFLICT(signature) DO UPDATE SET
                    label=excluded.label,
                    description=excluded.description,
                    keywords_json=excluded.keywords_json,
                    occurrences=workflow_patterns.occurrences+1,
                    successes=workflow_patterns.successes+excluded.successes,
                    confidence=excluded.confidence,
                    last_seen=excluded.last_seen,
                    project=COALESCE(excluded.project, workflow_patterns.project)""",
                (
                    signature, task, label, description, json.dumps(keywords),
                    int(success), confidence, now, now, project,
                ),
            )
            con.execute(
                """INSERT INTO workflow_observations
                (created_at, signature, task, success, project, prompt_hash)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (now, signature, task, int(success), project, prompt_hash),
            )
            row = con.execute(
                "SELECT * FROM workflow_patterns WHERE signature=?", (signature,)
            ).fetchone()
        return self._pattern_row(row)

    def bind_pattern_tool(self, signature: str, tool_slug: str) -> None:
        with self.connect() as con:
            con.execute(
                "UPDATE workflow_patterns SET tool_slug=?, last_seen=? WHERE signature=?",
                (tool_slug, datetime.now(UTC).isoformat(), signature),
            )

    def list_workflow_patterns(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute(
                """SELECT * FROM workflow_patterns
                ORDER BY occurrences DESC, last_seen DESC LIMIT ?""",
                (max(1, min(limit, 500)),),
            ).fetchall()
        return [self._pattern_row(row) for row in rows]

    def get_workflow_pattern(self, signature: str) -> dict[str, Any] | None:
        with self.connect() as con:
            row = con.execute(
                "SELECT * FROM workflow_patterns WHERE signature=?", (signature,)
            ).fetchone()
        return self._pattern_row(row) if row else None

    @staticmethod
    def _pattern_row(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["keywords"] = json.loads(item.pop("keywords_json") or "[]")
        item["occurrences"] = int(item["occurrences"])
        item["successes"] = int(item["successes"])
        item["confidence"] = float(item["confidence"])
        return item

    def provider_usage(self, provider: str, period: str = "day") -> dict[str, float | int]:
        if period not in {"day", "month"}:
            raise ValueError("period must be day or month")
        predicate = (
            "date(created_at)=date('now')"
            if period == "day"
            else "strftime('%Y-%m', created_at)=strftime('%Y-%m','now')"
        )
        with self.connect() as con:
            row = con.execute(
                f"""SELECT COUNT(*) requests, COALESCE(SUM(cost_usd),0) cost,
                COALESCE(SUM(input_tokens+output_tokens),0) tokens
                FROM requests WHERE provider=? AND status='ok' AND {predicate}""",
                (provider,),
            ).fetchone()
        return {"requests": int(row["requests"]), "cost": float(row["cost"]), "tokens": int(row["tokens"])}

    def provider_caps(self, provider: str, daily_request_cap: int, monthly_usd_cap: float) -> dict[str, Any]:
        day = self.provider_usage(provider, "day")
        month = self.provider_usage(provider, "month")
        return {
            "daily": day,
            "monthly": month,
            "daily_request_cap": daily_request_cap,
            "monthly_usd_cap": monthly_usd_cap,
            "daily_exhausted": bool(daily_request_cap and day["requests"] >= daily_request_cap),
            "monthly_exhausted": bool(monthly_usd_cap and month["cost"] >= monthly_usd_cap),
        }

    def dashboard_summary(self) -> dict[str, Any]:
        with self.connect() as con:
            today = con.execute(
                """SELECT COUNT(*) requests, COALESCE(SUM(input_tokens),0) input_tokens,
                COALESCE(SUM(output_tokens),0) output_tokens, COALESCE(SUM(cost_usd),0) cost
                FROM requests WHERE date(created_at)=date('now')"""
            ).fetchone()
            month = con.execute(
                """SELECT COUNT(*) requests, COALESCE(SUM(input_tokens),0) input_tokens,
                COALESCE(SUM(output_tokens),0) output_tokens, COALESCE(SUM(cost_usd),0) cost
                FROM requests WHERE strftime('%Y-%m', created_at)=strftime('%Y-%m','now')"""
            ).fetchone()
            providers = con.execute(
                """SELECT provider, COUNT(*) requests, COALESCE(SUM(input_tokens+output_tokens),0) tokens,
                COALESCE(SUM(cost_usd),0) cost, MAX(created_at) last_used
                FROM requests GROUP BY provider ORDER BY requests DESC"""
            ).fetchall()
            recent = con.execute(
                """SELECT created_at, task, provider, model, billing_class, input_tokens,
                output_tokens, cost_usd, latency_ms, status, session_id, parent_call_id,
                call_id, tool_name, phase, cache_hit, redundant_call, usage_status FROM requests
                ORDER BY id DESC LIMIT 30"""
            ).fetchall()
            routes = con.execute(
                """SELECT created_at, task, provider, model, score, reasons_json,
                requires_confirmation, session_id, parent_call_id, tool_name, phase
                FROM route_events ORDER BY id DESC LIMIT 30"""
            ).fetchall()
            preflights = con.execute(
                """SELECT plan_id, created_at, updated_at, task, mode, status, working_may_begin,
                requires_confirmation, estimated_input_tokens, max_output_tokens, routes_json,
                locks_json, working_started_at, completed_at, session_id, parent_call_id,
                tool_name
                FROM preflight_events ORDER BY created_at DESC LIMIT 30"""
            ).fetchall()
            quotas = con.execute(
                """SELECT q.provider, q.created_at, q.values_json FROM quota_snapshots q
                INNER JOIN (SELECT provider, MAX(id) id FROM quota_snapshots GROUP BY provider) latest
                ON q.id=latest.id"""
            ).fetchall()
            patterns = con.execute(
                """SELECT * FROM workflow_patterns
                ORDER BY occurrences DESC, last_seen DESC LIMIT 30"""
            ).fetchall()
            telemetry = con.execute(
                """SELECT COUNT(*) total_calls,
                SUM(CASE WHEN usage_status='reported' THEN 1 ELSE 0 END) reported_calls,
                SUM(CASE WHEN usage_status='not_reported' THEN 1 ELSE 0 END) unreported_calls,
                COALESCE(SUM(input_tokens+output_tokens),0) total_tokens,
                COALESCE(SUM(CASE WHEN usage_status='reported' THEN input_tokens+output_tokens ELSE 0 END),0) reported_tokens,
                COALESCE(SUM(cache_hit),0) cache_hits,
                COALESCE(SUM(redundant_call),0) redundant_calls,
                SUM(CASE WHEN session_id IS NULL OR call_id IS NULL OR parent_call_id IS NULL OR tool_name IS NULL
                    THEN 1 ELSE 0 END) unattributed_calls
                FROM requests"""
            ).fetchone()
        return {
            "today": dict(today),
            "month": dict(month),
            "providers": [dict(r) for r in providers],
            "recent": [dict(r) for r in recent],
            "routes": [
                {
                    **dict(r),
                    "requires_confirmation": bool(r["requires_confirmation"]),
                    "reasons": json.loads(r["reasons_json"]),
                }
                for r in routes
            ],
            "preflights": [
                {
                    **dict(row),
                    "working_may_begin": bool(row["working_may_begin"]),
                    "requires_confirmation": bool(row["requires_confirmation"]),
                    "routes": json.loads(row["routes_json"]),
                    "locks": json.loads(row["locks_json"]),
                }
                for row in preflights
            ],
            "quotas": [{**dict(r), "values": json.loads(r["values_json"])} for r in quotas],
            "patterns": [self._pattern_row(r) for r in patterns],
            "telemetry": dict(telemetry),
            "telemetry_health": {
                "usage_reporting_complete": int(telemetry["unreported_calls"] or 0) == 0,
                "attribution_complete": int(telemetry["unattributed_calls"] or 0) == 0,
                "unreported_calls": int(telemetry["unreported_calls"] or 0),
                "unattributed_calls": int(telemetry["unattributed_calls"] or 0),
                "ten_of_ten_ready": (
                    int(telemetry["unreported_calls"] or 0) == 0
                    and int(telemetry["unattributed_calls"] or 0) == 0
                ),
            },
        }

    def export_telemetry(self, limit: int = 1000) -> dict[str, Any]:
        """Export redacted request evidence suitable for independent validation."""
        if limit < 1:
            raise ValueError("limit must be positive")
        with self.connect() as con:
            rows = con.execute(
                """SELECT id, created_at, task, provider, model, billing_class,
                input_tokens, output_tokens, cost_usd, latency_ms, status, prompt_hash,
                session_id, call_id, parent_call_id, tool_name, phase, cache_hit,
                redundant_call, usage_status FROM requests ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return {
            "schema_version": 1,
            "redacted": True,
            "records": [dict(row) for row in rows],
        }
