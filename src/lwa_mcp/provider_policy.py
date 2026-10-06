"""Provider-order and failure-classification policy for Lwa routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class RoutingMode(StrEnum):
    CODEX_FIRST = "codex_first"
    THIRD_PARTY_FIRST = "third_party_first"
    MANUAL = "manual"

    @classmethod
    def parse(cls, value: str | RoutingMode) -> RoutingMode:
        if isinstance(value, cls):
            return value
        normalized = value.strip().lower().replace("-", "_")
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"Unknown routing mode: {value}") from exc


class Availability(StrEnum):
    AVAILABLE = "available"
    TEMPORARY_RATE_LIMIT = "temporary_rate_limit"
    QUOTA_EXHAUSTED = "quota_exhausted"
    UNAVAILABLE = "unavailable"
    AUTHENTICATION_FAILURE = "authentication_failure"
    SECURITY_DENIED = "security_denied"
    DISABLED = "disabled"


DEFAULT_ROUTES: dict[str, list[str]] = {
    RoutingMode.CODEX_FIRST.value: ["codex", "openrouter", "anthropic", "gemini"],
    RoutingMode.THIRD_PARTY_FIRST.value: ["openrouter", "anthropic", "gemini", "codex"],
}


@dataclass(frozen=True, slots=True)
class ProviderState:
    provider: str
    availability: Availability
    retry_at: datetime | None = None
    reset_at: datetime | None = None
    detail: str = ""


def classify_provider_failure(
    *,
    status_code: int | None = None,
    rate_limit_reached_type: str | None = None,
    quota_exhausted: bool = False,
    security_denied: bool = False,
    detail: str = "",
) -> Availability:
    """Normalize provider failure evidence without treating every error as quota.

    A retryable HTTP 429 is temporary. Permanent fallback is allowed only when
    the provider explicitly reports exhausted quota/credits or the caller has
    supplied equivalent authoritative evidence.
    """
    if security_denied:
        return Availability.SECURITY_DENIED
    if quota_exhausted:
        return Availability.QUOTA_EXHAUSTED
    reached = (rate_limit_reached_type or "").lower()
    if any(
        token in reached
        for token in ("quota", "credit", "monthly", "daily", "usage_limit", "limit_reached", "exhausted")
    ):
        return Availability.QUOTA_EXHAUSTED
    if status_code == 402:
        return Availability.QUOTA_EXHAUSTED
    if status_code == 429:
        return Availability.TEMPORARY_RATE_LIMIT
    if status_code in {401, 403}:
        return Availability.AUTHENTICATION_FAILURE
    if status_code is not None and status_code >= 400:
        return Availability.UNAVAILABLE
    return Availability.UNAVAILABLE


def classify_exception(exc: BaseException) -> Availability:
    """Classify a provider exception using structured evidence when available."""
    return classify_provider_failure(
        status_code=getattr(exc, "status_code", None),
        rate_limit_reached_type=getattr(exc, "rate_limit_reached_type", None),
        quota_exhausted=bool(getattr(exc, "quota_exhausted", False)),
        security_denied=bool(getattr(exc, "security_denied", False)),
        detail=str(exc),
    )


@dataclass(slots=True)
class ProviderRoutingPolicy:
    mode: RoutingMode = RoutingMode.CODEX_FIRST
    routes: dict[str, list[str]] = field(default_factory=lambda: {
        name: list(order) for name, order in DEFAULT_ROUTES.items()
    })
    manual_provider: str | None = None
    sticky_provider: str | None = None
    sticky_until: datetime | None = None
    session_sticky: dict[str, tuple[str, datetime | None]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.mode = RoutingMode.parse(self.mode)
        for name, order in DEFAULT_ROUTES.items():
            self.routes.setdefault(name, list(order))
        for name, order in self.routes.items():
            if not name or not order or len(order) != len(set(order)):
                raise ValueError(f"Route {name!r} must contain unique providers")

    def with_mode(self, mode: str | RoutingMode) -> ProviderRoutingPolicy:
        return ProviderRoutingPolicy(
            mode=RoutingMode.parse(mode),
            routes={name: list(order) for name, order in self.routes.items()},
            manual_provider=self.manual_provider,
        )

    def sticky_for(self, session_id: str | None = None, *, now: datetime | None = None) -> str | None:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        if session_id and session_id in self.session_sticky:
            provider, until = self.session_sticky[session_id]
            if until is None or until > current:
                return provider
            del self.session_sticky[session_id]
        if self.sticky_provider and (self.sticky_until is None or self.sticky_until > current):
            return self.sticky_provider
        if self.sticky_provider:
            self.clear_sticky()
        return None

    def sticky_until_for(self, session_id: str | None = None) -> datetime | None:
        if session_id and session_id in self.session_sticky:
            return self.session_sticky[session_id][1]
        return self.sticky_until

    def provider_order(
        self, *, now: datetime | None = None, session_id: str | None = None
    ) -> list[str]:
        sticky = self.sticky_for(session_id, now=now)
        if sticky:
            return [sticky]
        if self.mode is RoutingMode.MANUAL:
            return [self.manual_provider] if self.manual_provider else []
        return list(self.routes[self.mode.value])

    def fallback_allowed(self, state: ProviderState) -> bool:
        return state.availability is Availability.QUOTA_EXHAUSTED

    def stick(
        self, provider: str, *, reset_at: datetime | None = None, session_id: str | None = None
    ) -> None:
        until = reset_at.astimezone(UTC) if reset_at else None
        if session_id:
            self.session_sticky[session_id] = (provider, until)
        else:
            self.sticky_provider = provider
            self.sticky_until = until

    def clear_sticky(self, session_id: str | None = None) -> None:
        if session_id:
            self.session_sticky.pop(session_id, None)
            return
        self.sticky_provider = None
        self.sticky_until = None
        self.session_sticky.clear()
