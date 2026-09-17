"""Fail-closed, data-free provider pipeline status and accessibility checks."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from datetime import UTC, datetime
from typing import Any, ClassVar

from .catalog import Catalog
from .config import LoadedConfig
from .providers import build_adapter
from .providers.base import ProviderError, redact_error


class PipelineManager:
    """Track provider readiness without ever inspecting or forwarding prompts."""

    _MANUAL_STATES: ClassVar[set[str]] = {"ready", "degraded", "blocked", "maintenance"}
    _CACHE_SCHEMA: ClassVar[str] = "pipeline-probe-v1"
    _SUCCESS_TTL_SECONDS: ClassVar[float] = 60.0
    _FAILURE_TTL_SECONDS: ClassVar[float] = 15.0

    def __init__(self, config: LoadedConfig, catalog: Catalog):
        self.config = config
        self.catalog = catalog
        self._marks: dict[str, dict[str, Any]] = {}
        self._probe_cache: dict[str, dict[str, Any]] = {}
        self._inflight: dict[str, asyncio.Task[dict[str, Any]]] = {}

    def _fingerprint(self, name: str) -> str:
        provider = self.config.settings.providers.get(name)
        if provider is None:
            return "unknown"
        material = {
            "schema": self._CACHE_SCHEMA,
            "provider": provider.model_dump(
                mode="json", exclude={"request_headers", "api_key_env", "api_key_envs", "billing_api_key_env", "quota_key_env"}
            ),
            "credential_slots": [
                [env, bool(os.getenv(env, ""))]
                for env in provider.credential_env_names()
            ],
            "account_configured": bool(
                not provider.account_id_env or os.getenv(provider.account_id_env, "")
            ),
            "models": sorted(model.key for model in self.catalog.all() if model.provider == name),
        }
        encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _credentialed(self, provider: Any) -> bool:
        names = provider.credential_env_names()
        present = not names or any(os.getenv(name, "") for name in names)
        if provider.account_id_env:
            present = present and bool(os.getenv(provider.account_id_env, ""))
        return present

    def _base_status(self, name: str) -> dict[str, Any]:
        provider = self.config.settings.providers.get(name)
        now = datetime.now(UTC).isoformat()
        if provider is None:
            return {
                "provider": name,
                "status": "unknown_provider",
                "check_mode": "offline",
                "checked_at": now,
                "data_transmitted": False,
                "cost_incurred": False,
                "detail": "provider is not configured",
            }

        credentialed = self._credentialed(provider)
        models = [model for model in self.catalog.all() if model.provider == name]
        known_health = self.catalog.health.get(name)
        live_verified = bool(known_health and known_health.healthy is True)
        if not provider.enabled:
            status, detail = "blocked", provider.disabled_reason or "provider disabled"
        elif not provider.base_url:
            status, detail = "unavailable", "provider has no endpoint configured"
        elif not credentialed:
            status, detail = "missing_credentials", "required credential or account is unavailable"
        elif known_health and known_health.healthy is False:
            status, detail = "unhealthy", known_health.detail
        else:
            status, detail = "ready", "configured for a data-free preflight"

        row = {
            "provider": name,
            "status": status,
            "enabled": provider.enabled,
            "configured": True,
            "credentialed": credentialed,
            "endpoint_configured": bool(provider.base_url),
            "catalog_models": len(models),
            "billing_class": provider.billing_class.value,
            "check_mode": "offline",
            "checked_at": now,
            "data_transmitted": False,
            "cost_incurred": False,
            "detail": detail,
            # `ready` is retained for compatibility and means that a seed route
            # may be considered. These fields prevent it being mistaken for a
            # live reachability or quota claim.
            "readiness": "live_verified" if live_verified else "configured",
            "live_verified": live_verified,
            "quota_verified": False,
        }
        if known_health:
            row["known_health"] = known_health.model_dump(mode="json")
        if name in self._marks:
            row["manual_mark"] = dict(self._marks[name])
        return row

    def status(self, name: str | None = None) -> list[dict[str, Any]] | dict[str, Any]:
        """Return local pipeline state; this method never performs network I/O."""
        if name:
            return self._base_status(name)
        return [self._base_status(provider) for provider in self.config.settings.providers]

    def mark(self, name: str, status: str, detail: str = "") -> dict[str, Any]:
        """Record an operator status mark without changing routing configuration."""
        if status not in self._MANUAL_STATES:
            raise ValueError(f"status must be one of {sorted(self._MANUAL_STATES)}")
        if name not in self.config.settings.providers:
            raise ValueError(f"unknown provider: {name}")
        self._marks[name] = {
            "status": status,
            "detail": detail[:500],
            "source": "operator",
            "marked_at": datetime.now(UTC).isoformat(),
        }
        return self._base_status(name)

    async def check(self, name: str | None = None, *, probe: bool = False) -> Any:
        """Check access without sending a user prompt.

        The default is strictly offline. ``probe=True`` calls only the
        adapter health/model-metadata endpoint; no RouteRequest is created.
        """
        names = [name] if name else list(self.config.settings.providers)
        rows: list[dict[str, Any]] = []
        for provider_name in names:
            row = self._base_status(provider_name)
            if probe and row.get("status") == "ready":
                row = await self._cached_probe(provider_name)
            rows.append(row)
        return rows[0] if name else rows

    async def _cached_probe(self, name: str) -> dict[str, Any]:
        fingerprint = self._fingerprint(name)
        now = time.monotonic()
        cached = self._probe_cache.get(name)
        if cached and cached["fingerprint"] == fingerprint:
            age = now - cached["stored_at"]
            ttl = self._SUCCESS_TTL_SECONDS if cached["success"] else self._FAILURE_TTL_SECONDS
            if age < ttl:
                row = dict(cached["row"])
                row.update({"cache_hit": True, "cache_age_seconds": round(age, 3), "network_calls": 0})
                return row

        task = self._inflight.get(name)
        if task is None:
            task = asyncio.create_task(self._perform_probe(name, fingerprint))
            self._inflight[name] = task
        try:
            row = dict(await asyncio.shield(task))
        finally:
            if self._inflight.get(name) is task:
                self._inflight.pop(name, None)
        return row

    async def _perform_probe(self, name: str, fingerprint: str) -> dict[str, Any]:
        row = self._base_status(name)
        row.update({"cache_hit": False, "cache_age_seconds": 0.0, "network_calls": 0})
        try:
            provider = self.config.settings.providers[name]
            healthy, detail = await build_adapter(provider).health()
            row.update(
                {
                    "status": "reachable" if healthy else "unhealthy",
                    "check_mode": "zero_payload_probe",
                    "endpoint_reachable": healthy,
                    "data_transmitted": False,
                    "cost_incurred": False,
                    "detail": redact_error(detail),
                    "network_calls": 1,
                    "readiness": "probe_verified" if healthy else "probe_failed",
                    "live_verified": healthy,
                }
            )
        except Exception as exc:  # noqa: BLE001
            row.update(
                {
                    "status": "unreachable",
                    "check_mode": "zero_payload_probe",
                    "endpoint_reachable": False,
                    "data_transmitted": False,
                    "cost_incurred": False,
                    "detail": redact_error(str(exc)),
                    "network_calls": 1,
                }
            )
        self._probe_cache[name] = {
            "fingerprint": fingerprint,
            "stored_at": time.monotonic(),
            "success": row.get("status") == "reachable",
            "row": dict(row),
        }
        return row

    def invalidate_probe_cache(self, name: str | None = None) -> int:
        """Invalidate one provider or all cached probes."""
        if name:
            return int(self._probe_cache.pop(name, None) is not None)
        count = len(self._probe_cache)
        self._probe_cache.clear()
        return count

    def assert_can_send(self, name: str) -> None:
        """Block obvious inaccessible routes before a provider receives data."""
        row = self._base_status(name)
        if row["status"] in {"blocked", "unavailable", "missing_credentials", "unhealthy", "unknown_provider"}:
            raise ProviderError(f"pipeline {name} is not ready: {row['detail']}")
