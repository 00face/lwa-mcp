from __future__ import annotations

import math
import os
from collections import Counter
from dataclasses import dataclass

from .catalog import Catalog
from .config import LoadedConfig
from .contracts import candidate_supported_parameters
from .db import UsageDB
from .models import BillingClass, ConsentMode, ModelCandidate, RouteDecision, RouteRequest

BILLING_BONUS = {
    BillingClass.FREE: 35.0,
    BillingClass.FREE_QUOTA: 28.0,
    BillingClass.USER_PAYS: 18.0,
    BillingClass.PAID: 0.0,
    BillingClass.UNKNOWN: -8.0,
}

QUALITY_MINIMUMS = {"economy": 0.0, "balanced": 35.0, "high": 55.0}


@dataclass(slots=True)
class Scored:
    candidate: ModelCandidate
    score: float
    reasons: list[str]


@dataclass(slots=True)
class RouteRejection:
    provider: str
    model: str
    reason: str


class NoRouteError(RuntimeError):
    """Raised when preflight cannot find an eligible model.

    The message is intentionally safe to surface to an operator: it contains
    model/provider names and policy or capability gates, never credential
    values or prompt contents.
    """

    def __init__(self, request: RouteRequest, rejections: list[RouteRejection]):
        self.task = request.task.value
        self.required_capabilities = sorted(capability.value for capability in request.required_capabilities)
        self.rejections = rejections
        super().__init__(self._message(request, rejections))

    @staticmethod
    def _message(request: RouteRequest, rejections: list[RouteRejection]) -> str:
        if not rejections:
            detail = "no catalog candidates were available"
        else:
            counts = Counter(rejection.reason for rejection in rejections)
            ordered_reasons = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            summary = "; ".join(
                f"{reason} ({count} model{'s' if count != 1 else ''})"
                for reason, count in ordered_reasons[:8]
            )
            examples = "; ".join(
                f"{rejection.provider}/{rejection.model}: {rejection.reason}"
                for rejection in rejections[:8]
            )
            detail = f"{summary}. Examples: {examples}"
        return (
            "No configured model satisfies this task and capability set "
            f"(task={request.task.value}, required_capabilities="
            f"{','.join(sorted(capability.value for capability in request.required_capabilities))}); "
            f"{detail}"
        )


def estimate_tokens(text: str) -> int:
    # Conservative tokenizer-independent estimate for routing only.
    return max(1, math.ceil(len(text) / 3.6))


class Router:
    def __init__(self, config: LoadedConfig, catalog: Catalog, db: UsageDB):
        self.config = config
        self.catalog = catalog
        self.db = db

    def consent_mode(self) -> ConsentMode:
        stored = self.db.get_setting("consent_mode")
        return ConsentMode(stored) if stored else self.config.settings.consent_mode

    def set_consent_mode(self, mode: ConsentMode) -> None:
        self.db.set_setting("consent_mode", mode.value)

    def _rejection_reason(
        self, candidate: ModelCandidate, request: RouteRequest, input_tokens: int
    ) -> str | None:
        if not candidate.enabled:
            return candidate.disabled_reason or "model disabled"
        if candidate.provider in request.excluded_providers:
            return "provider excluded by request"
        if not request.required_capabilities.issubset(candidate.capabilities):
            missing = sorted(capability.value for capability in request.required_capabilities - candidate.capabilities)
            return f"missing capabilities: {','.join(missing)}"
        if request.reasoning_effort is not None:
            requested_effort = getattr(request.reasoning_effort, "value", str(request.reasoning_effort))
            if not candidate.reasoning_levels:
                return f"reasoning_effort={requested_effort} unsupported by model"
            if requested_effort not in candidate.reasoning_levels:
                supported = ",".join(candidate.reasoning_levels) or "none"
                return f"reasoning_effort={requested_effort} unsupported (advertised: {supported})"
        supported_parameters = candidate_supported_parameters(candidate)
        response_format = request.metadata.get("response_format")
        if response_format is not None and supported_parameters and "response_format" not in supported_parameters and "structured_outputs" not in supported_parameters:
            return "response_format unsupported by model"
        if input_tokens + request.max_output_tokens > candidate.context_length:
            return (
                f"context too small (needs {input_tokens + request.max_output_tokens}, "
                f"model allows {candidate.context_length})"
            )
        provider = self.config.settings.providers.get(candidate.provider)
        if not provider:
            return "provider is not configured"
        if not provider.enabled:
            return provider.disabled_reason or "provider disabled"
        # A live refresh that explicitly marked a provider unhealthy must gate
        # its seed models too. Otherwise stale seed entries can win routing
        # after discovery or authentication has failed.
        provider_health = self.catalog.health.get(candidate.provider)
        if provider_health is not None and provider_health.healthy is False:
            return f"provider unhealthy: {provider_health.detail}"
        credential_envs = provider.credential_env_names()
        if credential_envs and not any(os.getenv(name, "") for name in credential_envs):
            return f"missing credential ({','.join(credential_envs)})"
        if provider.account_id_env and not os.getenv(provider.account_id_env, ""):
            return f"missing account identifier ({provider.account_id_env})"
        caps = self.db.provider_caps(
            candidate.provider, provider.daily_request_cap, provider.monthly_usd_cap
        )
        if caps["daily_exhausted"]:
            return "daily request cap exhausted"
        if caps["monthly_exhausted"]:
            return "monthly spend cap exhausted"
        if candidate.billing_class == BillingClass.PAID and not (request.allow_paid and self.config.settings.allow_paid):
            return "paid route disabled"
        if candidate.billing_class == BillingClass.USER_PAYS and not (
            request.allow_user_pays and self.config.settings.allow_user_pays
        ):
            return "user-pays route disabled"
        return None

    def _score(
        self,
        candidate: ModelCandidate,
        request: RouteRequest,
        input_tokens: int,
        rejection_sink: list[RouteRejection] | None = None,
    ) -> Scored | None:
        rejection = self._rejection_reason(candidate, request, input_tokens)
        if rejection is not None:
            if rejection_sink is not None:
                rejection_sink.append(RouteRejection(candidate.provider, candidate.model, rejection))
            return None
        score = candidate.task_scores.get(request.task.value, 40.0)
        reasons = [f"task score {score:.0f}"]
        if request.reasoning_effort is not None:
            reasons.append(f"reasoning effort {getattr(request.reasoning_effort, 'value', request.reasoning_effort)}")
        if self.config.settings.prefer_free:
            quality_weight = {"economy": 1.0, "balanced": 0.60, "high": 0.15}[request.quality]
            bonus = BILLING_BONUS[candidate.billing_class] * quality_weight
            score += bonus
            reasons.append(
                f"billing {candidate.billing_class.value} {bonus:+.1f} at {request.quality} quality"
            )
        if request.preferred_providers:
            preferred_index = next(
                (
                    index
                    for index, provider in enumerate(request.preferred_providers, start=1)
                    if provider == candidate.provider
                ),
                None,
            )
            if preferred_index is not None:
                reasons.append(f"preferred provider order #{preferred_index}")
        context_headroom = candidate.context_length - input_tokens - request.max_output_tokens
        if context_headroom > 64_000:
            score += 6
            reasons.append("large context headroom +6")
        elif context_headroom < 2048:
            score -= 12
            reasons.append("tight context -12")
        if request.quality == "high" and candidate.task_scores.get(request.task.value, 0) >= 75:
            score += 12
            reasons.append("high-quality specialist +12")
        if request.quality == "economy" and candidate.billing_class in {BillingClass.FREE, BillingClass.FREE_QUOTA}:
            score += 8
            reasons.append("economy free preference +8")
        return Scored(candidate, score, reasons)

    def decide(self, request: RouteRequest) -> RouteDecision:
        input_tokens = estimate_tokens((request.system_prompt or "") + request.prompt)
        rejections: list[RouteRejection] = []
        scored = [self._score(model, request, input_tokens, rejections) for model in self.catalog.all()]
        valid = [item for item in scored if item is not None]
        if not valid:
            raise NoRouteError(request, rejections)
        # Explicit secondary keys make equal-score routing reproducible across
        # catalog refreshes and Python implementations.
        preferred_order: dict[str, int] = {}
        for index, provider in enumerate(request.preferred_providers, start=1):
            preferred_order.setdefault(provider, index)
        preferred_count = len(preferred_order)
        valid.sort(
            key=lambda item: (
                preferred_order.get(item.candidate.provider, preferred_count + 1),
                -item.score,
                item.candidate.provider,
                item.candidate.model,
            )
        )
        chosen = valid[0]
        if chosen.score < QUALITY_MINIMUMS[request.quality]:
            paid_candidates = [
                item for item in valid if item.candidate.billing_class in {BillingClass.PAID, BillingClass.USER_PAYS}
            ]
            if paid_candidates:
                chosen = paid_candidates[0]
                chosen.reasons.append("free candidates below requested quality floor")
        candidate = chosen.candidate
        estimated_cost = None
        if candidate.input_cost_per_million is not None:
            estimated_cost = input_tokens * candidate.input_cost_per_million / 1_000_000
            estimated_cost += request.max_output_tokens * (candidate.output_cost_per_million or 0) / 1_000_000
        mode = self.consent_mode()
        requires = mode == ConsentMode.ALWAYS or (
            mode == ConsentMode.PAID_ONLY
            and candidate.billing_class in {BillingClass.PAID, BillingClass.USER_PAYS}
        )
        decision = RouteDecision(
            candidate=candidate,
            score=chosen.score,
            reasons=chosen.reasons,
            estimated_input_tokens=input_tokens,
            estimated_max_cost_usd=estimated_cost,
            requires_confirmation=requires,
        )
        self.db.record_route(request, decision)
        return decision
