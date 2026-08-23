from __future__ import annotations

import asyncio
import socket
import sqlite3
import tempfile
from datetime import UTC, datetime
from os import getenv
from pathlib import Path
from typing import Any
from uuid import uuid4

from .catalog import Catalog
from .config import DEFAULT_DB_FILE, DEFAULT_TOOL_LIBRARY_DIR, LoadedConfig, load_config
from .consent import ConsentGate
from .contracts import (
    billing_route_intent,
    contract_for_task,
    route_intent,
    validate_request_contract,
)
from .db import UsageDB
from .models import (
    Capability,
    CompletionResult,
    ConsentMode,
    LibraryToolKind,
    LibraryToolStatus,
    RouteDecision,
    RouteRequest,
    TaskKind,
    parse_consent_mode,
)
from .patterns import PatternDetector
from .pipeline_manager import PipelineManager
from .preflight import PreflightStore
from .prompts import DEFAULT_PROMPTS
from .providers import build_adapter
from .providers.base import redact_error
from .routing import Router
from .syntax import (
    parse_task_kind,
    validate_public_prompt_template,
    validate_quality,
    validate_reasoning_effort,
)
from .terminal_ui import get_codex_identity, render_execution_telemetry, response_display
from .tool_library import ToolLibrary

# Consensus is a fan-out operation, so an unbounded draft or review transcript
# can exceed the smallest eligible provider's context window. These limits are
# deliberately conservative and tokenizer-independent.
CONSENSUS_DRAFT_MAX_CHARS = 16_000
CONSENSUS_TRANSCRIPT_MAX_CHARS = 20_000
CONSENSUS_REVIEW_MAX_CHARS = 4_000


def _bounded_text(value: str, limit: int) -> str:
    """Keep both the beginning and end of long operator input."""
    if len(value) <= limit:
        return value
    head = max(1, int(limit * 0.72))
    tail = max(1, limit - head)
    omitted = len(value) - head - tail
    return (
        value[:head]
        + f"\n\n[content compacted by LWA: {omitted} characters omitted]\n\n"
        + value[-tail:]
    )


def _compact_consensus_transcript(reviews: list[Any], failures: list[dict[str, Any]], limit: int) -> str:
    """Bound consensus material while retaining every provider's identity."""
    sections: list[str] = []
    per_review = max(600, min(CONSENSUS_REVIEW_MAX_CHARS, limit // max(1, len(reviews))))
    for review in reviews:
        sections.append(
            f"### {review.provider} / {review.model}\n"
            f"{_bounded_text(review.text, per_review)}"
        )
    if failures:
        sections.append(
            "### Voter failures\n"
            + "\n".join(
                f"- {item['provider']} / {item['model']}: unavailable ({item['error']})"
                for item in failures
            )
        )
    return _bounded_text("\n\n".join(sections), limit)


def rank_model_tiers(models: list[Any], providers: dict[str, Any], limit: int = 100) -> list[dict[str, Any]]:
    """Rank configured models without opening the usage database."""
    rows = []
    for model in models:
        provider = providers.get(model.provider)
        supported_parameters = sorted(model.supported_parameters)
        rows.append(
            {
                "provider": model.provider,
                "model": model.model,
                "display_name": model.display_name,
                "service_tiers": list(model.service_tiers),
                "supported_parameters": supported_parameters,
                "reasoning_levels": list(model.reasoning_levels),
                "capabilities": sorted(capability.value for capability in model.capabilities),
                "source": model.source,
                "enabled": model.enabled,
                "free_plan_max_tokens": model.free_plan_max_tokens,
                "pro_plan_max_tokens": model.pro_plan_max_tokens,
                "billing_class": model.billing_class.value,
                "subscription_plan": provider.subscription_plan if provider else "unknown",
                "subscription_status": (
                    provider.subscription_status.value if provider else "unknown"
                ),
                "subscription_monthly_token_limit": (
                    provider.subscription_monthly_token_limit if provider else None
                ),
                "context_length": model.context_length,
            }
        )
    rows.sort(
        key=lambda row: (
            row["free_plan_max_tokens"] is None,
            -(row["free_plan_max_tokens"] or 0),
            -(row["pro_plan_max_tokens"] or 0),
            row["provider"],
            row["model"],
        ),
    )
    for rank, row in enumerate(rows[: max(0, limit)], start=1):
        row["rank"] = rank
    return rows[: max(0, limit)]


class RouterService:
    def __init__(self, config: LoadedConfig | None = None):
        self.session_id = uuid4().hex
        self.config = config or load_config()
        try:
            self._initialize_components(self.config)
        except sqlite3.OperationalError as exc:
            if not self._should_use_runtime_fallback(exc):
                raise
            self.config = self._runtime_fallback_config(self.config)
            self._initialize_components(self.config)
        self._initialize_lock = asyncio.Lock()
        self._initialized = False

    def _initialize_components(self, config: LoadedConfig) -> None:
        self.db = UsageDB(config.db_path)
        self.catalog = Catalog(config)
        self.pipeline_manager = PipelineManager(config, self.catalog)
        self.router = Router(config, self.catalog, self.db)
        self.consent = ConsentGate(config.settings.confirmation_ttl_seconds)
        self.preflights = PreflightStore(config.settings.confirmation_ttl_seconds)
        self.library = ToolLibrary(config.tool_library_path)
        self.patterns = PatternDetector(config, self.db, self.library)

    def _should_use_runtime_fallback(self, exc: sqlite3.OperationalError) -> bool:
        if "unable to open database file" not in str(exc).lower():
            return False
        return self.config.db_path == DEFAULT_DB_FILE and self.config.tool_library_path == DEFAULT_TOOL_LIBRARY_DIR

    @staticmethod
    def _runtime_fallback_config(config: LoadedConfig) -> LoadedConfig:
        runtime_root = Path(
            getenv("LWA_MCP_RUNTIME_ROOT", Path(tempfile.gettempdir()) / "lwa-mcp-codex")
        )
        return LoadedConfig(
            settings=config.settings,
            config_path=config.config_path,
            env_path=config.env_path,
            db_path=runtime_root / "state" / "lwa.sqlite3",
            tool_library_path=runtime_root / "data" / "tool-library",
        )

    async def initialize(self) -> None:
        """Start the shared doctor/catalog and tool-library services once.

        MCP and dashboard hosts can both call this hook during startup.  The
        lock prevents concurrent hosts from rebuilding the shared state twice,
        while the flag makes repeated calls cheap. Boot stays local-only; live
        catalog refresh remains behind the explicit refresh tool.
        """
        if self._initialized:
            return
        async with self._initialize_lock:
            if self._initialized:
                return
            # ToolLibrary creates its layout in the constructor; rebuilding the
            # catalog here also makes startup self-healing if the catalog was
            # removed.
            self.library.rebuild_catalog()
            self._initialized = True

    def build_request(
        self,
        task: TaskKind | str,
        prompt: str,
        *,
        system_prompt: str | None = None,
        quality: str = "balanced",
        reasoning_effort: str | None = None,
        allow_paid: bool = False,
        allow_user_pays: bool = False,
        max_output_tokens: int = 1200,
        preferred_providers: list[str] | None = None,
        excluded_providers: list[str] | None = None,
        required_capabilities: set[Capability] | None = None,
        metadata: dict[str, Any] | None = None,
        tool_name: str | None = None,
    ) -> RouteRequest:
        task_kind = parse_task_kind(task)
        validate_quality(quality)
        validate_reasoning_effort(reasoning_effort)
        contract = contract_for_task(task_kind)
        doctrine = self.config.settings.task_prompts.get(task_kind.value) or DEFAULT_PROMPTS[task_kind]
        merged_system = doctrine if not system_prompt else f"{doctrine}\n\nAdditional instruction:\n{system_prompt}"
        if task_kind == TaskKind.IMAGE_GENERATION or task_kind == TaskKind.VIDEO_GENERATION:
            allow_user_pays = False
        elif task_kind == TaskKind.CONSENSUS and (metadata or {}).get("consensus_role") != "synthesis":
            allow_paid = False
            allow_user_pays = False
        merged_metadata = dict(metadata or {})
        merged_metadata.setdefault("session_id", self.session_id)
        merged_metadata.setdefault("call_id", uuid4().hex)
        merged_metadata.setdefault("tool_name", tool_name or "router_service")
        merged_metadata.setdefault("phase", "request")
        merged_metadata.setdefault("pipeline", contract.pipeline)
        if reasoning_effort is not None:
            merged_metadata.setdefault("reasoning_effort", reasoning_effort)
        merged_metadata.setdefault("route_intent", route_intent(task_kind, allow_paid, allow_user_pays))
        merged_metadata.setdefault("route_intent_billing_class", billing_route_intent(allow_paid, allow_user_pays))
        if task_kind == TaskKind.IMAGE_GENERATION:
            merged_metadata.setdefault("aspect_ratio", "1:1")
            merged_metadata.setdefault("output_format", "png")
        elif task_kind == TaskKind.VIDEO_GENERATION:
            merged_metadata.setdefault("seconds", "4")
            merged_metadata.setdefault("size", "1280x720")
        elif task_kind == TaskKind.CONSENSUS:
            merged_metadata["route_intent"] = "consensus:free_only"
            merged_metadata["route_intent_billing_class"] = "free_only"
            merged_metadata.setdefault("consensus_preflight", False)
            merged_metadata.setdefault("consensus_role", "voter")
        if required_capabilities is None:
            required_capabilities = set(contract.required_capabilities)
        elif not contract.required_capabilities.issubset(required_capabilities):
            raise ValueError(
                f"{task_kind.value} requires capabilities "
                f"{sorted(cap.value for cap in contract.required_capabilities)}"
            )
        return RouteRequest(
            task=task_kind,
            prompt=prompt,
            system_prompt=merged_system,
            quality=quality,  # type: ignore[arg-type]
            reasoning_effort=reasoning_effort,  # type: ignore[arg-type]
            allow_paid=allow_paid,
            allow_user_pays=allow_user_pays,
            max_output_tokens=max_output_tokens,
            preferred_providers=preferred_providers or [],
            excluded_providers=excluded_providers or [],
            required_capabilities=required_capabilities,
            metadata=merged_metadata,
        )

    @staticmethod
    def _finalize_request(request: RouteRequest) -> RouteRequest:
        """Freeze line endings and metadata without altering prompt semantics."""
        prompt = request.prompt.replace("\r\n", "\n").replace("\r", "\n")
        system_prompt = (
            request.system_prompt.replace("\r\n", "\n").replace("\r", "\n")
            if request.system_prompt is not None
            else None
        )
        metadata = {
            **request.metadata,
            "strict_preflight": True,
            "prompt_finalized_before_work": True,
            "dynamic_rerouting_during_work": False,
        }
        return request.model_copy(
            update={"prompt": prompt, "system_prompt": system_prompt, "metadata": metadata}
        )

    async def prepare_task(self, request: RouteRequest) -> dict[str, Any]:
        """Lock prompt, token budget, consent state, and model before provider work."""
        # Preflight must remain deterministic and cheap. Live model discovery is
        # an explicit operator action through refresh_model_catalog(); seed and
        # previously refreshed candidates are sufficient for route selection.
        locked_request = self._finalize_request(request)
        validate_request_contract(locked_request)
        decision = self.router.decide(locked_request)
        prepared = self.preflights.create(
            mode="single",
            requests=[locked_request],
            decisions=[decision],
            route_roles=[("primary", 0)],
        )
        self.db.record_preflight(prepared.summary)
        return {
            "status": prepared.summary.status,
            "phase": "preflight_complete",
            "message": self.preflight_announcement(prepared.summary),
            "preflight": prepared.summary.model_dump(mode="json"),
            "library_suggestions": self.suggest_library_tools(
                locked_request.prompt,
                task=locked_request.task,
                limit=self.config.settings.max_library_suggestions,
            ),
        }

    async def prepare_consensus(
        self,
        prompt: str,
        voters: int = 3,
        quality: str = "balanced",
        allow_paid: bool = False,
        excluded_providers: list[str] | None = None,
        reasoning_effort: str | None = None,
    ) -> dict[str, Any]:
        """Preselect every eligible free model and a synthesis model.

        Consensus is deliberately a free-model rite: paid and user-pays routes
        are never voters. ``voters`` remains as a compatibility argument for
        callers, but the contract is now all eligible free providers rather than
        an arbitrary cap.
        """
        prompt = _bounded_text(prompt, CONSENSUS_DRAFT_MAX_CHARS)
        base = self._finalize_request(
            self.build_request(
                TaskKind.CONSENSUS,
                prompt,
                quality=quality,
                reasoning_effort=reasoning_effort,
                allow_paid=allow_paid,
                allow_user_pays=False,
                max_output_tokens=1000,
                metadata={"consensus_preflight": True},
            )
        )
        requests: list[RouteRequest] = []
        decisions: list[RouteDecision] = []
        excluded: list[str] = list(excluded_providers or [])
        while True:
            req = base.model_copy(update={"excluded_providers": list(excluded)})
            try:
                validate_request_contract(req)
                decision = self.router.decide(req)
            except RuntimeError:
                break
            if decision.candidate.billing_class.value not in {"free", "free_quota"}:
                raise RuntimeError(
                    "Consensus voter policy violation: selected a non-free model "
                    f"({decision.candidate.provider}/{decision.candidate.model})"
                )
            requests.append(req)
            decisions.append(decision)
            excluded.append(decision.candidate.provider)

        if not decisions:
            raise RuntimeError("No eligible free models are available for consensus")

        synthesis_template = (
            "Synthesize the following independent reviews. Preserve disagreements, list shared "
            "conclusions, state unresolved risks, and give a final recommendation with confidence."
            "\n\n{{CONSENSUS_TRANSCRIPT}}"
        )
        # Routing only needs a representative prompt. The previous repeated
        # placeholder inflated the estimate into a context-length failure.
        reserved_transcript = "\n\n".join(
            f"### REVIEW {index}\n[provider review]"
            for index in range(1, len(decisions) + 1)
        )
        routing_prompt = synthesis_template.replace("{{CONSENSUS_TRANSCRIPT}}", reserved_transcript)
        synthesis_request = self._finalize_request(
            self.build_request(
                TaskKind.CONSENSUS,
                routing_prompt,
                quality=quality,
                reasoning_effort=reasoning_effort,
                allow_paid=allow_paid,
                allow_user_pays=False,
                max_output_tokens=1400,
                excluded_providers=list(excluded),
                metadata={
                    "consensus_preflight": True,
                    "consensus_role": "synthesis",
                    "synthesis_template_locked": True,
                },
            )
        )
        validate_request_contract(synthesis_request)
        try:
            synthesis_decision = self.router.decide(synthesis_request)
        except RuntimeError:
            # Reuse is chosen here, during preflight, when provider diversity is exhausted.
            synthesis_request = synthesis_request.model_copy(update={"excluded_providers": []})
            validate_request_contract(synthesis_request)
            synthesis_decision = self.router.decide(synthesis_request)

        prepared = self.preflights.create(
            mode="consensus",
            requests=requests,
            decisions=decisions,
            route_roles=[("consensus_voter", index) for index in range(len(decisions))],
            synthesis_request=synthesis_request,
            synthesis_decision=synthesis_decision,
            synthesis_template=synthesis_template,
        )
        self.db.record_preflight(prepared.summary)
        return {
            "status": prepared.summary.status,
            "phase": "preflight_complete",
            "message": self.preflight_announcement(prepared.summary),
            "preflight": prepared.summary.model_dump(mode="json"),
        }

    def approve_preflight(self, confirmation_token: str) -> dict[str, Any]:
        summary = self.preflights.approve(confirmation_token)
        self.db.update_preflight_status(summary.plan_id, "ready", working_may_begin=True)
        return {
            "status": "ready",
            "phase": "preflight_complete",
            "message": self.preflight_announcement(summary),
            "preflight": summary.model_dump(mode="json"),
        }

    async def run_prepared_task(
        self, plan_token: str, next_tier_suggestion: str | None = None
    ) -> dict[str, Any]:
        """Begin Working only after consuming a fully locked and approved preflight plan."""
        prepared = self.preflights.consume(plan_token)
        summary = prepared.summary
        started_at = datetime.now(UTC).isoformat()
        self.db.update_preflight_status(summary.plan_id, "working", working_may_begin=True)
        try:
            if prepared.mode == "consensus":
                result = await self._execute_prepared_consensus(prepared)
            else:
                completion = await self.execute(prepared.requests[0], prepared.decisions[0])
                result = {
                    "status": "completed",
                    "decision": prepared.decisions[0].model_dump(mode="json"),
                    "result": completion.model_dump(mode="json"),
                }
        except Exception as exc:  # noqa: BLE001
            self.db.update_preflight_status(summary.plan_id, "repreflight_required")
            return {
                "status": "repreflight_required",
                "phase": "work_stopped",
                "working_started_at": started_at,
                "message": (
                    "The locked route failed. Working stopped; a new preflight is required "
                    "before selecting or switching to another model."
                ),
                "error": redact_error(str(exc)),
                "preflight": summary.model_dump(mode="json"),
            }
        self.db.update_preflight_status(summary.plan_id, "completed")
        completed = {
            **result,
            "phase": "work_complete",
            "working_started_at": started_at,
            "preflight": summary.model_dump(mode="json"),
        }
        identity = get_codex_identity()
        display = response_display(completed, identity)
        provider_name = display.get("provider")
        provider = self.config.settings.providers.get(provider_name or "")
        if provider:
            display.update(
                {
                    "subscription_plan": provider.subscription_plan,
                    "subscription_status": provider.subscription_status.value,
                }
            )
        display["telemetry"] = render_execution_telemetry(
            {**completed, "display": display}, identity
        )
        completed["display"] = display
        guidance = self.post_response_tier_guidance(
            prepared, next_tier_suggestion=next_tier_suggestion
        )
        if guidance:
            completed["next_tier_guidance"] = guidance
        return completed

    def _tier_guidance_enabled(self) -> bool:
        stored = self.db.get_setting("post_response_tier_guidance")
        if stored is not None:
            return stored.lower() in {"1", "true", "yes", "on"}
        return self.config.settings.post_response_tier_guidance

    def _tier_guidance_mode(self) -> str:
        return self.db.get_setting("post_response_tier_guidance_mode") or self.config.settings.post_response_tier_guidance_mode

    def set_tier_guidance(self, enabled: bool, mode: str = "local") -> dict[str, Any]:
        if mode not in {"local", "codex_request"}:
            raise ValueError("mode must be local or codex_request")
        self.db.set_setting("post_response_tier_guidance", "true" if enabled else "false")
        self.db.set_setting("post_response_tier_guidance_mode", mode)
        return {"enabled": enabled, "mode": mode}

    def post_response_tier_guidance(
        self, prepared: Any, *, next_tier_suggestion: str | None = None
    ) -> dict[str, Any] | None:
        if not self._tier_guidance_enabled() and not next_tier_suggestion:
            return None
        route = prepared.decisions[0] if prepared.decisions else None
        current = route.candidate if route else None
        if next_tier_suggestion:
            return {
                "source": "host_ingested",
                "suggestion": next_tier_suggestion[:500],
                "directive": "Treat this as advisory; require a fresh preflight before selecting it.",
                "accepted": False,
            }
        if self._tier_guidance_mode() == "codex_request":
            return {
                "source": "codex_request",
                "suggestion": None,
                "directive": "Ask the Codex machine spirit to suggest the next model tier, then submit it as next_tier_suggestion.",
                "accepted": False,
            }
        if current is None:
            return None
        alternatives = [
            model for model in self.catalog.all()
            if model.key != current.key and model.enabled and model.provider in self.config.settings.providers
        ]
        alternatives.sort(
            key=lambda model: model.task_scores.get(prepared.requests[0].task.value, 0),
            reverse=True,
        )
        next_model = alternatives[0] if alternatives else None
        return {
            "source": "local",
            "current": f"{current.provider}/{current.model}",
            "suggested": f"{next_model.provider}/{next_model.model}" if next_model else None,
            "directive": "Use the suggestion only after a fresh preflight; do not alter the current locked route.",
            "accepted": False,
        }

    async def _execute_prepared_consensus(self, prepared: Any) -> dict[str, Any]:
        voter_results = await asyncio.gather(
            *(
                self.execute(request, decision)
                for request, decision in zip(
                    prepared.requests, prepared.decisions, strict=True
                )
            ),
            return_exceptions=True,
        )
        reviews = []
        failures = []
        for decision, result in zip(prepared.decisions, voter_results, strict=True):
            if isinstance(result, Exception):
                failures.append(
                    {
                        "provider": decision.candidate.provider,
                        "model": decision.candidate.model,
                        "error": redact_error(str(result)),
                    }
                )
            else:
                reviews.append(result)
        if not reviews:
            detail = "; ".join(f"{item['provider']}: {item['error']}" for item in failures)
            raise RuntimeError(f"All consensus voters failed: {detail}")
        if not prepared.synthesis_request or not prepared.synthesis_decision:
            raise RuntimeError("Prepared consensus plan is missing its locked synthesis route")
        synthesis_context = max(
            2_000,
            (prepared.synthesis_decision.candidate.context_length - prepared.synthesis_request.max_output_tokens - 512)
            * 3,
        )
        transcript = _compact_consensus_transcript(
            reviews,
            failures,
            min(CONSENSUS_TRANSCRIPT_MAX_CHARS, synthesis_context),
        )
        template = prepared.synthesis_template or "{{CONSENSUS_TRANSCRIPT}}"
        synthesis_prompt = template.replace("{{CONSENSUS_TRANSCRIPT}}", transcript)
        synthesis_request = prepared.synthesis_request.model_copy(
            update={"prompt": synthesis_prompt}
        )
        synthesis_failures = []
        synthesis = None
        synthesis_decisions = [prepared.synthesis_decision] + [
            decision
            for decision in prepared.decisions
            if decision.candidate.provider != prepared.synthesis_decision.candidate.provider
            and decision.candidate.provider in {review.provider for review in reviews}
        ]
        for synthesis_decision in synthesis_decisions:
            try:
                synthesis = await self.execute(synthesis_request, synthesis_decision)
                break
            except Exception as exc:  # noqa: BLE001
                synthesis_failures.append(
                    {
                        "provider": synthesis_decision.candidate.provider,
                        "model": synthesis_decision.candidate.model,
                        "error": redact_error(str(exc)),
                    }
                )
        if synthesis is None:
            detail = "; ".join(f"{item['provider']}: {item['error']}" for item in synthesis_failures)
            raise RuntimeError(f"All consensus synthesis providers failed: {detail}")
        return {
            "status": "completed",
            "reviews": [review.model_dump(mode="json") for review in reviews],
            "voter_failures": failures,
            "synthesis_failures": synthesis_failures,
            "synthesis": synthesis.model_dump(mode="json"),
        }

    async def preview(self, request: RouteRequest) -> RouteDecision:
        decision = self.router.decide(request)
        if decision.requires_confirmation:
            decision.confirmation_token = self.consent.issue(request, decision)
        return decision

    async def execute(self, request: RouteRequest, decision: RouteDecision) -> CompletionResult:
        provider_cfg = self.config.settings.providers[decision.candidate.provider]
        self.pipeline_manager.assert_can_send(decision.candidate.provider)
        adapter = build_adapter(provider_cfg)
        validate_request_contract(request)
        try:
            result = await adapter.complete(decision.candidate, request)
        except Exception as exc:
            safe_error = redact_error(str(exc))
            self.db.record_result(request, decision, None, "error", {"error": safe_error})
            self.patterns.observe_request(request, success=False)
            raise
        self.db.record_result(request, decision, result, "ok")
        self.patterns.observe_request(request, success=True)
        return result

    async def smart_complete(self, request: RouteRequest) -> dict[str, Any]:
        """Legacy name retained for callers; strict mode returns preflight only."""
        return await self.prepare_task(request)

    def confirm_and_run(self, token: str) -> dict[str, Any]:
        """Legacy name retained; approval is separate from execution in strict mode."""
        return self.approve_preflight(token)

    async def consensus(
        self,
        prompt: str,
        voters: int = 3,
        quality: str = "balanced",
        allow_paid: bool = False,
        reasoning_effort: str | None = None,
    ) -> dict[str, Any]:
        """Legacy name retained; strict mode returns consensus preflight only."""
        return await self.prepare_consensus(
            prompt,
            voters,
            quality,
            allow_paid,
            reasoning_effort=reasoning_effort,
        )

    def list_library_tools(self, status: str | None = None) -> list[dict[str, Any]]:
        parsed = LibraryToolStatus(status) if status else None
        return [item.model_dump(mode="json") for item in self.library.list(parsed)]

    def suggest_library_tools(
        self,
        context: str,
        *,
        task: TaskKind | str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        if not self.config.settings.suggest_library_tools:
            return []
        return self.library.search(
            context,
            task=task,
            limit=limit or self.config.settings.max_library_suggestions,
            active_only=True,
        )

    def read_library_tool(self, slug: str) -> dict[str, Any]:
        return self.library.read_bundle(slug)

    def create_library_tool(
        self,
        *,
        name: str,
        description: str,
        task: TaskKind | str,
        prompt_template: str,
        tags: list[str] | None = None,
        triggers: list[str] | None = None,
        activate: bool = True,
    ) -> dict[str, Any]:
        tool = self.library.create_prompt_tool(
            name=name,
            description=description,
            task=task,
            prompt_template=validate_public_prompt_template(prompt_template),
            tags=tags,
            triggers=triggers,
            activate=activate,
        )
        return tool.model_dump(mode="json")

    def register_script_tool(
        self,
        *,
        name: str,
        description: str,
        task: TaskKind | str,
        source: str,
        filename: str = "tool.py",
        tags: list[str] | None = None,
        triggers: list[str] | None = None,
    ) -> dict[str, Any]:
        tool = self.library.register_script(
            name=name,
            description=description,
            task=task,
            source=source,
            filename=filename,
            tags=tags,
            triggers=triggers,
        )
        return tool.model_dump(mode="json")

    def set_library_tool_status(
        self, slug: str, status: str, *, approved: bool | None = None
    ) -> dict[str, Any]:
        tool = self.library.set_status(slug, LibraryToolStatus(status), approved=approved)
        return tool.model_dump(mode="json")

    def observe_workflow(
        self,
        *,
        workflow_name: str,
        description: str,
        task: TaskKind | str,
        sample: str = "",
        project: str | None = None,
        success: bool = True,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        return self.patterns.observe(
            task=task,
            sample=sample or description,
            workflow_name=workflow_name,
            description=description,
            project=project,
            success=success,
            tags=tags,
        )

    def analyze_workflow_patterns(self, limit: int = 100) -> dict[str, Any]:
        return self.patterns.analyze(limit)

    async def run_library_tool(
        self,
        slug: str,
        input_text: str,
        *,
        quality: str = "balanced",
        allow_paid: bool = False,
        allow_user_pays: bool = False,
        reasoning_effort: str | None = None,
    ) -> dict[str, Any]:
        tool = self.library.get(slug)
        if tool.status != LibraryToolStatus.ACTIVE:
            raise ValueError(f"Library tool {slug!r} is not active.")
        if tool.kind == LibraryToolKind.PROMPT_RECIPE:
            prompt = tool.prompt_template.replace("{input}", input_text)
            request = self.build_request(
                tool.task,
                prompt,
                quality=quality,
                reasoning_effort=reasoning_effort,
                allow_paid=allow_paid,
                allow_user_pays=allow_user_pays,
                metadata={
                    "library_tool_slug": tool.slug,
                    "skip_pattern_detection": True,
                },
            )
            result = await self.prepare_task(request)
            result["library_tool"] = tool.model_dump(mode="json")
            return result
        if not tool.approved or not self.config.settings.allow_reviewed_script_execution:
            return {
                "status": "review_required",
                "message": (
                    "Script tools remain non-executable until approved and "
                    "allow_reviewed_script_execution is enabled."
                ),
                "library_tool": tool.model_dump(mode="json"),
            }
        import asyncio
        import sys

        entrypoint = self.library.tools_dir / tool.slug / tool.entrypoint
        if entrypoint.parent != (self.library.tools_dir / tool.slug) or not entrypoint.is_file():
            raise ValueError("Library tool entrypoint is invalid or missing.")
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(entrypoint),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(entrypoint.parent),
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input_text.encode("utf-8")), timeout=120
            )
        except TimeoutError:
            process.kill()
            stdout, stderr = await process.communicate()
            max_output_bytes = 1_000_000
            return {
                "status": "timed_out",
                "returncode": process.returncode,
                "stdout": stdout[:max_output_bytes].decode("utf-8", errors="replace"),
                "stderr": stderr[:max_output_bytes].decode("utf-8", errors="replace"),
                "library_tool": tool.model_dump(mode="json"),
            }
        max_output_bytes = 1_000_000
        return {
            "status": "completed" if process.returncode == 0 else "failed",
            "returncode": process.returncode,
            "stdout": stdout[:max_output_bytes].decode("utf-8", errors="replace"),
            "stderr": stderr[:max_output_bytes].decode("utf-8", errors="replace"),
            "library_tool": tool.model_dump(mode="json"),
        }

    async def refresh_provider_quotas(self) -> dict[str, Any]:
        import os

        async def one(name: str) -> tuple[str, dict[str, Any]]:
            cfg = self.config.settings.providers[name]
            if not cfg.enabled or not cfg.quota_path:
                return name, {"status": "not_supported"}
            key_envs = cfg.credential_env_names(billing=True) or cfg.credential_env_names()
            if key_envs and not any(os.getenv(key, "") for key in key_envs):
                return name, {"status": "not_configured", "missing": key_envs}
            try:
                payload = await build_adapter(cfg).fetch_quota()
                if payload is None:
                    return name, {"status": "not_supported"}
                self.db.record_quota_snapshot(name, payload)
                return name, {"status": "ok", "values": payload}
            except Exception as exc:  # noqa: BLE001
                return name, {"status": "error", "error": redact_error(str(exc))}

        rows = await asyncio.gather(*(one(name) for name in self.config.settings.providers))
        return {name: value for name, value in rows}

    def preflight_announcement(self, summary: Any) -> str:
        routes = ", ".join(
            f"{route.role}: {route.decision.candidate.provider}/{route.decision.candidate.model}"
            for route in summary.routes
        )
        gate = "approval required" if summary.requires_confirmation and not summary.working_may_begin else "ready"
        return (
            f"Preflight {gate}. Prompt, token budget, consensus plan, and routes are locked "
            f"before Working: {routes}."
        )

    def route_announcement(self, decision: RouteDecision) -> str:
        price = decision.candidate.billing_class.value.replace("_", " ")
        cost = (
            f", estimated ceiling ${decision.estimated_max_cost_usd:.4f}"
            if decision.estimated_max_cost_usd is not None
            else ""
        )
        return (
            f"Routing to {decision.candidate.provider} / {decision.candidate.model} "
            f"({price}{cost}) for this task."
        )

    def set_consent_mode(self, mode: ConsentMode | str) -> str:
        parsed = parse_consent_mode(mode)
        self.router.set_consent_mode(parsed)
        return parsed.value

    def status(self) -> dict[str, Any]:
        summary = self.db.dashboard_summary()
        dashboard_host = self.config.settings.dashboard_host
        dashboard_port = self.config.settings.dashboard_port
        return {
            "consent_mode": self.router.consent_mode().value,
            "catalog_models": len(self.catalog.all()),
            "health": [item.model_dump(mode="json") for item in self.catalog.health.values()],
            "pipelines": self.pipeline_manager.status(),
            "usage": summary,
            "library": self.library.summary(),
            "pattern_count": len(summary.get("patterns", [])),
            "dashboard_host": dashboard_host,
            "dashboard_port": dashboard_port,
            "dashboard_url": f"http://{dashboard_host}:{dashboard_port}",
            "dashboard_running": self._dashboard_running(dashboard_host, dashboard_port),
        }

    async def pipeline_status(self, provider: str | None = None, *, probe: bool = False) -> Any:
        return await self.pipeline_manager.check(provider, probe=probe)

    def mark_pipeline(self, provider: str, status: str, detail: str = "") -> dict[str, Any]:
        return self.pipeline_manager.mark(provider, status, detail)

    def invalidate_pipeline_probe_cache(self, provider: str | None = None) -> int:
        return self.pipeline_manager.invalidate_probe_cache(provider)

    @staticmethod
    def _dashboard_running(host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except OSError:
            return False

    def catalog_json(self) -> list[dict[str, Any]]:
        return [m.model_dump(mode="json") for m in self.catalog.all()]

    def model_tiers(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return configured models ranked by declared free-plan token capacity."""
        return rank_model_tiers(self.catalog.all(), self.config.settings.providers, limit)

    def providers_json(self) -> list[dict[str, Any]]:
        import os

        rows = []
        for name, cfg in self.config.settings.providers.items():
            credential_envs = cfg.credential_env_names()
            configured = not credential_envs or any(os.getenv(name, "") for name in credential_envs)
            if cfg.account_id_env:
                configured = configured and bool(os.getenv(cfg.account_id_env, ""))
            rows.append(
                {
                    "name": name,
                    "enabled": cfg.enabled,
                    "experimental": cfg.experimental,
                    "configured": configured,
                    "adapter": cfg.adapter,
                    "billing_class": cfg.billing_class.value,
                    "subscription_plan": cfg.subscription_plan,
                    "subscription_status": cfg.subscription_status.value,
                    "subscription_monthly_token_limit": cfg.subscription_monthly_token_limit,
                    "credential_slots": list(
                        dict.fromkeys(
                            [*cfg.credential_env_names(), *cfg.credential_env_names(billing=True)]
                        )
                    ),
                    "billing_credential_configured": any(
                        os.getenv(name, "") for name in cfg.credential_env_names(billing=True)
                    ),
                    "monthly_usd_cap": cfg.monthly_usd_cap,
                    "daily_request_cap": cfg.daily_request_cap,
                    "disabled_reason": cfg.disabled_reason,
                    "caps": self.db.provider_caps(name, cfg.daily_request_cap, cfg.monthly_usd_cap),
                }
            )
        return rows
