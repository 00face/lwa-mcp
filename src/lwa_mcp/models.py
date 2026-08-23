from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class BillingClass(StrEnum):
    FREE = "free"
    FREE_QUOTA = "free_quota"
    USER_PAYS = "user_pays"
    PAID = "paid"
    UNKNOWN = "unknown"


class SubscriptionStatus(StrEnum):
    UNKNOWN = "unknown"
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class ConsentMode(StrEnum):
    ALWAYS_ASK = "always_ask"
    PAID_ONLY = "paid_only"
    AUTOMATIC = "automatic"

    # Backward-compatible aliases retained for older docs and configurations.
    ALWAYS = ALWAYS_ASK
    NEVER = AUTOMATIC


def parse_consent_mode(value: str | ConsentMode) -> ConsentMode:
    if isinstance(value, ConsentMode):
        return value
    normalized = value.strip().lower().replace("-", "_")
    aliases = {
        "always": ConsentMode.ALWAYS_ASK,
        "always_ask": ConsentMode.ALWAYS_ASK,
        "ask_always": ConsentMode.ALWAYS_ASK,
        "paid_only": ConsentMode.PAID_ONLY,
        "automatic": ConsentMode.AUTOMATIC,
        "never": ConsentMode.AUTOMATIC,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        raise ValueError(f"Unknown consent mode: {value}") from exc


class Capability(StrEnum):
    TEXT = "text"
    REASONING = "reasoning"
    TOOLS = "tools"
    STRUCTURED = "structured"
    VISION = "vision"
    IMAGE = "image"
    VIDEO = "video"
    EMBEDDING = "embedding"
    RERANK = "rerank"


class TaskKind(StrEnum):
    QUICK_RESPONSE = "quick_response"
    QUERY = "query"
    CONVERSATION_COMPRESSION = "conversation_compression"
    TOKEN_OPTIMIZATION = "token_optimization"
    DOCUMENT_EDITING = "document_editing"
    SITREP = "sitrep"
    PLANNING = "planning"
    CONSENSUS = "consensus"
    VERIFICATION = "verification"
    CODING_AUX = "coding_aux"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"


class ReasoningEffort(StrEnum):
    """Lwa's provider-neutral reasoning controls.

    ``instant`` is deliberately deterministic: adapters map it to the
    provider's no-reasoning/lowest-effort setting rather than enabling a
    provider-side automatic escalation.
    """

    INSTANT = "instant"
    MEDIUM = "medium"
    HIGH = "high"


class LibraryToolKind(StrEnum):
    PROMPT_RECIPE = "prompt_recipe"
    SCRIPT = "script"


class LibraryToolStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class ProviderConfig(BaseModel):
    name: str
    enabled: bool = True
    experimental: bool = False
    adapter: Literal["openai", "openai_media", "gemini", "puter", "replicate", "stability"] = "openai"
    base_url: str | None = None
    api_key_env: str | None = None
    api_key_envs: list[str] = Field(default_factory=list)
    billing_api_key_env: str | None = None
    account_id_env: str | None = None
    models_path: str = "/models"
    chat_path: str = "/chat/completions"
    request_headers: dict[str, str] = Field(default_factory=dict)
    quota_path: str | None = None
    quota_key_env: str | None = None
    billing_class: BillingClass = BillingClass.UNKNOWN
    subscription_plan: str = "unknown"
    subscription_status: SubscriptionStatus = SubscriptionStatus.UNKNOWN
    subscription_monthly_token_limit: int | None = None
    supports_live_models: bool = True
    monthly_usd_cap: float = 0.0
    daily_request_cap: int = 0
    timeout_seconds: float = 90.0
    # Discovery is control-plane traffic. Keep it bounded even when a provider
    # exposes a very large or paginated model catalog.
    catalog_page_limit: int = Field(default=10, ge=1, le=100)
    catalog_model_limit: int = Field(default=500, ge=1, le=10_000)
    disabled_reason: str | None = None

    def credential_env_names(self, *, billing: bool = False) -> list[str]:
        if billing:
            names = [self.billing_api_key_env, self.quota_key_env]
            names = [name for name in names if name]
            if names:
                return list(dict.fromkeys(names))
        names = [*self.api_key_envs]
        if self.api_key_env:
            names.insert(0, self.api_key_env)
        return list(dict.fromkeys(names))


class ModelCandidate(BaseModel):
    provider: str
    model: str
    display_name: str | None = None
    billing_class: BillingClass = BillingClass.UNKNOWN
    capabilities: set[Capability] = Field(default_factory=lambda: {Capability.TEXT})
    service_tiers: list[str] = Field(default_factory=list)
    supported_parameters: set[str] = Field(default_factory=set)
    reasoning_levels: list[str] = Field(default_factory=list)
    context_length: int = 8192
    free_plan_max_tokens: int | None = None
    pro_plan_max_tokens: int | None = None
    free_plan_input_tokens: int | None = None
    free_plan_output_tokens: int | None = None
    input_cost_per_million: float | None = None
    output_cost_per_million: float | None = None
    task_scores: dict[str, float] = Field(default_factory=dict)
    enabled: bool = True
    disabled_reason: str | None = None
    source: Literal["seed", "live"] = "seed"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.provider}:{self.model}"


class RouteRequest(BaseModel):
    task: TaskKind
    prompt: str = Field(min_length=1, max_length=2_000_000)
    system_prompt: str | None = Field(default=None, max_length=200_000)
    required_capabilities: set[Capability] = Field(default_factory=lambda: {Capability.TEXT})
    max_output_tokens: int = Field(default=1200, ge=1, le=100_000)
    quality: Literal["economy", "balanced", "high"] = "balanced"
    reasoning_effort: ReasoningEffort | None = None
    # Spending is opt-in at the request boundary. Consent governs execution of
    # an eligible paid route; it must not make paid routes eligible by default.
    allow_paid: bool = False
    allow_user_pays: bool = False
    preferred_providers: list[str] = Field(default_factory=list)
    excluded_providers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RouteDecision(BaseModel):
    candidate: ModelCandidate
    score: float
    reasons: list[str]
    estimated_input_tokens: int
    estimated_max_cost_usd: float | None = None
    requires_confirmation: bool = False
    confirmation_token: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LockedRoute(BaseModel):
    role: Literal["primary", "consensus_voter", "consensus_synthesis"]
    order: int
    decision: RouteDecision


class PreflightSummary(BaseModel):
    plan_id: str
    plan_token: str
    mode: Literal["single", "consensus"] = "single"
    task: TaskKind
    reasoning_effort: ReasoningEffort | None = None
    status: Literal["ready", "confirmation_required", "consumed", "expired"] = "ready"
    working_may_begin: bool = False
    requires_confirmation: bool = False
    confirmation_token: str | None = None
    prompt_hash: str
    system_prompt_hash: str
    estimated_input_tokens: int
    max_output_tokens: int
    routes: list[LockedRoute] = Field(default_factory=list)
    locks: dict[str, bool] = Field(default_factory=dict)
    prompt_lock_scope: Literal["complete", "template"] = "complete"
    session_id: str | None = None
    call_id: str | None = None
    parent_call_id: str | None = None
    tool_name: str = "router_service"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at_epoch: float


class CompletionResult(BaseModel):
    provider: str
    model: str
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None
    latency_ms: int = 0
    finish_reason: str | None = None
    response_id: str | None = None
    transport: Literal["gateway", "direct", "local"] = "gateway"
    rate_limits: dict[str, str] = Field(default_factory=dict)
    raw_usage: dict[str, Any] = Field(default_factory=dict)
    usage_reported: bool = False
    credential_env: str | None = None


class PendingRoute(BaseModel):
    token: str
    request: RouteRequest
    decision: RouteDecision
    expires_at_epoch: float


class ProviderHealth(BaseModel):
    provider: str
    configured: bool
    enabled: bool
    experimental: bool = False
    healthy: bool | None = None
    detail: str = ""
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LibraryTool(BaseModel):
    slug: str
    name: str
    description: str
    version: str = "0.1.0"
    kind: LibraryToolKind = LibraryToolKind.PROMPT_RECIPE
    status: LibraryToolStatus = LibraryToolStatus.ACTIVE
    task: TaskKind = TaskKind.QUERY
    prompt_template: str = "{input}"
    entrypoint: str = "run.py"
    tags: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    origin: str = "operator"
    review_state: str = "approved"
    safety_state: str = "safe"
    created_by: str = "operator"
    pattern_signature: str | None = None
    evidence_count: int = 0
    confidence: float = 0.0
    approved: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowPattern(BaseModel):
    signature: str
    task: TaskKind
    label: str
    description: str
    keywords: list[str] = Field(default_factory=list)
    occurrences: int = 0
    successes: int = 0
    confidence: float = 0.0
    first_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tool_slug: str | None = None
    project: str | None = None
