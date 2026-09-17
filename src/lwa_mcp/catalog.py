from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from .config import LoadedConfig
from .models import ModelCandidate, ProviderHealth
from .providers import build_adapter
from .providers.base import redact_error


class Catalog:
    def __init__(self, config: LoadedConfig):
        self.config = config
        self._models: dict[str, ModelCandidate] = {m.key: m for m in config.settings.models}
        self._last_refresh = 0.0
        self.health: dict[str, ProviderHealth] = {}

    def all(self) -> list[ModelCandidate]:
        return sorted(self._models.values(), key=lambda m: (m.provider, m.model))

    def by_provider(self) -> dict[str, list[ModelCandidate]]:
        grouped: dict[str, list[ModelCandidate]] = defaultdict(list)
        for model in self.all():
            grouped[model.provider].append(model)
        return dict(grouped)

    async def refresh(self, force: bool = False) -> dict[str, int]:
        ttl = self.config.settings.catalog_refresh_minutes * 60
        if not force and time.time() - self._last_refresh < ttl:
            return {"models": len(self._models), "refreshed": 0}

        async def one(provider_name: str):
            provider = self.config.settings.providers[provider_name]
            credential_envs = provider.credential_env_names()
            configured = bool(
                not credential_envs
                or any(__import__("os").getenv(name, "") for name in credential_envs)
            )
            if provider.account_id_env:
                configured = configured and bool(__import__("os").getenv(provider.account_id_env, ""))
            if not provider.enabled:
                self.health[provider_name] = ProviderHealth(
                    provider=provider_name,
                    configured=configured,
                    enabled=False,
                    experimental=provider.experimental,
                    healthy=None,
                    detail=provider.disabled_reason or "disabled",
                )
                return []
            if not configured and credential_envs:
                self.health[provider_name] = ProviderHealth(
                    provider=provider_name,
                    configured=False,
                    enabled=True,
                    experimental=provider.experimental,
                    healthy=None,
                    detail=f"missing one of {', '.join(credential_envs)}",
                )
                return []
            adapter = build_adapter(provider)
            try:
                models = await adapter.list_models()
                models = models[: provider.catalog_model_limit]
                self.health[provider_name] = ProviderHealth(
                    provider=provider_name,
                    configured=configured,
                    enabled=True,
                    experimental=provider.experimental,
                    healthy=True,
                    detail=(
                        f"{len(models)} live models"
                        + (" (bounded)" if len(models) == provider.catalog_model_limit else "")
                        if models
                        else "configured"
                    ),
                )
                return models
            except Exception as exc:  # noqa: BLE001
                detail = redact_error(str(exc))
                # A provider with no successful live evidence must not leave its
                # seed routes looking production-ready after discovery fails.
                # Keep the provider configured for explicit recovery, but mark
                # it experimental and disable only the unverified seed models.
                provider.experimental = True
                if not any(
                    model.provider == provider_name and model.source == "live"
                    for model in self._models.values()
                ):
                    reason = f"Experimental provider: live model discovery failed; {detail}"
                    for model in self._models.values():
                        if model.provider == provider_name and model.source == "seed":
                            model.enabled = False
                            model.disabled_reason = reason
                self.health[provider_name] = ProviderHealth(
                    provider=provider_name,
                    configured=configured,
                    enabled=True,
                    experimental=True,
                    healthy=False,
                    detail=detail,
                )
                return []

        names = list(self.config.settings.providers)
        results = await asyncio.gather(*(one(name) for name in names))
        refreshed = 0
        for models in results:
            for model in models:
                existing = self._models.get(model.key)
                if existing:
                    model.task_scores = existing.task_scores
                    model.metadata = {**model.metadata, **existing.metadata}
                    if existing.billing_class.value != "unknown":
                        model.billing_class = existing.billing_class
                    if existing.free_plan_max_tokens is not None:
                        model.free_plan_max_tokens = existing.free_plan_max_tokens
                    if existing.pro_plan_max_tokens is not None:
                        model.pro_plan_max_tokens = existing.pro_plan_max_tokens
                self._models[model.key] = model
                refreshed += 1
        self._last_refresh = time.time()
        return {"models": len(self._models), "refreshed": refreshed}
