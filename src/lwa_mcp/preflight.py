from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from .models import LockedRoute, PreflightSummary, RouteDecision, RouteRequest


@dataclass(slots=True)
class PreparedExecution:
    summary: PreflightSummary
    mode: Literal["single", "consensus"]
    requests: list[RouteRequest]
    decisions: list[RouteDecision]
    synthesis_request: RouteRequest | None = None
    synthesis_decision: RouteDecision | None = None
    synthesis_template: str | None = None
    approved: bool = False


class PreflightStore:
    """In-memory, single-use execution-plan store.

    A plan freezes prompts, token budgets, consensus roles, and model choices before
    provider execution starts. The store deliberately does not persist raw prompts.
    """

    def __init__(self, ttl_seconds: int = 600):
        self.ttl_seconds = ttl_seconds
        secret = os.getenv("LWA_PREFLIGHT_SECRET") or os.getenv("CASTOR_POLLUX_CONFIRMATION_SECRET")
        self._secret = (secret or secrets.token_hex(32)).encode("utf-8")
        self._plans: dict[str, PreparedExecution] = {}
        self._confirmations: dict[str, str] = {}

    @staticmethod
    def _digest(text: str | None) -> str:
        return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

    def _signed_token(self, plan_id: str, purpose: str) -> str:
        nonce = secrets.token_urlsafe(18)
        material = f"{plan_id}:{purpose}:{nonce}:{int(time.time() + self.ttl_seconds)}"
        signature = hmac.new(self._secret, material.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
        return f"{nonce}.{signature}"

    def create(
        self,
        *,
        mode: Literal["single", "consensus"],
        requests: list[RouteRequest],
        decisions: list[RouteDecision],
        route_roles: list[tuple[str, int]],
        synthesis_request: RouteRequest | None = None,
        synthesis_decision: RouteDecision | None = None,
        synthesis_template: str | None = None,
    ) -> PreparedExecution:
        if not requests or not decisions or len(requests) != len(decisions):
            raise ValueError("Preflight requires matching request and decision lists")
        if len(route_roles) != len(decisions):
            raise ValueError("Every locked decision needs a route role")

        plan_id = secrets.token_hex(12)
        plan_token = self._signed_token(plan_id, "execute")
        requires_confirmation = any(item.requires_confirmation for item in decisions)
        all_routes = [
            LockedRoute(role=role, order=order, decision=decision)
            for (role, order), decision in zip(route_roles, decisions, strict=True)
        ]
        if synthesis_decision is not None:
            all_routes.append(
                LockedRoute(role="consensus_synthesis", order=len(all_routes), decision=synthesis_decision)
            )
            requires_confirmation = requires_confirmation or synthesis_decision.requires_confirmation

        confirmation_token = (
            self._signed_token(plan_id, "confirm") if requires_confirmation else None
        )
        now = datetime.now(UTC)
        first_request = requests[0]
        estimated_input = sum(item.estimated_input_tokens for item in decisions)
        if synthesis_decision is not None:
            estimated_input += synthesis_decision.estimated_input_tokens
        max_output = sum(request.max_output_tokens for request in requests)
        if synthesis_request is not None:
            max_output += synthesis_request.max_output_tokens

        summary = PreflightSummary(
            plan_id=plan_id,
            plan_token=plan_token,
            mode=mode,
            task=first_request.task,
            reasoning_effort=first_request.reasoning_effort,
            status="confirmation_required" if requires_confirmation else "ready",
            working_may_begin=not requires_confirmation,
            requires_confirmation=requires_confirmation,
            confirmation_token=confirmation_token,
            prompt_hash=self._digest(first_request.prompt),
            system_prompt_hash=self._digest(first_request.system_prompt),
            estimated_input_tokens=estimated_input,
            max_output_tokens=max_output,
            routes=all_routes,
            locks={
                "prompt": True,
                "token_budget": True,
                "consensus_plan": True,
                "model_routes": True,
                "dynamic_rerouting_during_work": False,
            },
            prompt_lock_scope="template" if mode == "consensus" else "complete",
            session_id=first_request.metadata.get("session_id"),
            call_id=first_request.metadata.get("call_id"),
            parent_call_id=first_request.metadata.get("parent_call_id"),
            tool_name=first_request.metadata.get("tool_name", "router_service"),
            created_at=now,
            expires_at_epoch=time.time() + self.ttl_seconds,
        )
        prepared = PreparedExecution(
            summary=summary,
            mode=mode,
            requests=requests,
            decisions=decisions,
            synthesis_request=synthesis_request,
            synthesis_decision=synthesis_decision,
            synthesis_template=synthesis_template,
            approved=not requires_confirmation,
        )
        self._plans[plan_token] = prepared
        if confirmation_token:
            self._confirmations[confirmation_token] = plan_token
        return prepared

    def approve(self, confirmation_token: str) -> PreflightSummary:
        self.purge()
        plan_token = self._confirmations.pop(confirmation_token, None)
        if not plan_token:
            raise ValueError("Unknown, expired, or already-used preflight confirmation token")
        prepared = self._plans.get(plan_token)
        if prepared is None:
            raise ValueError("Prepared execution no longer exists")
        prepared.approved = True
        prepared.summary.status = "ready"
        prepared.summary.working_may_begin = True
        prepared.summary.confirmation_token = None
        return prepared.summary

    def consume(self, plan_token: str) -> PreparedExecution:
        self.purge()
        prepared = self._plans.pop(plan_token, None)
        if prepared is None:
            raise ValueError("Unknown, expired, or already-used preflight plan token")
        if not prepared.approved:
            self._plans[plan_token] = prepared
            raise PermissionError("Preflight approval is required before Working may begin")
        for token, target in list(self._confirmations.items()):
            if target == plan_token:
                self._confirmations.pop(token, None)
        prepared.summary.status = "consumed"
        prepared.summary.working_may_begin = True
        return prepared

    def purge(self) -> None:
        now = time.time()
        expired = [
            token
            for token, prepared in self._plans.items()
            if prepared.summary.expires_at_epoch < now
        ]
        for token in expired:
            self._plans.pop(token, None)
            for confirmation, target in list(self._confirmations.items()):
                if target == token:
                    self._confirmations.pop(confirmation, None)

    def public_json(self, prepared: PreparedExecution) -> dict:
        return json.loads(prepared.summary.model_dump_json())
