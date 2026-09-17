from __future__ import annotations

from dataclasses import dataclass

from .models import BillingClass, Capability, ModelCandidate, RouteRequest, TaskKind
from .syntax import parse_task_kind


@dataclass(frozen=True, slots=True)
class PipelineContract:
    task: TaskKind
    pipeline: str
    required_capabilities: frozenset[Capability]
    default_allow_paid: bool
    default_allow_user_pays: bool
    required_metadata_keys: frozenset[str] = frozenset()
    forbidden_metadata_keys: frozenset[str] = frozenset()
    allowed_billing_classes: frozenset[BillingClass] | None = None


_TEXT = frozenset({Capability.TEXT})
_TEXT_REASONING = frozenset({Capability.TEXT, Capability.REASONING})
_IMAGE = frozenset({Capability.IMAGE})
_VIDEO = frozenset({Capability.VIDEO})


TASK_CONTRACTS: dict[TaskKind, PipelineContract] = {
    TaskKind.QUICK_RESPONSE: PipelineContract(
        task=TaskKind.QUICK_RESPONSE,
        pipeline="text",
        required_capabilities=_TEXT,
        default_allow_paid=True,
        default_allow_user_pays=True,
    ),
    TaskKind.QUERY: PipelineContract(
        task=TaskKind.QUERY,
        pipeline="text",
        required_capabilities=_TEXT,
        default_allow_paid=True,
        default_allow_user_pays=True,
    ),
    TaskKind.CONVERSATION_COMPRESSION: PipelineContract(
        task=TaskKind.CONVERSATION_COMPRESSION,
        pipeline="text",
        required_capabilities=_TEXT,
        default_allow_paid=True,
        default_allow_user_pays=True,
    ),
    TaskKind.TOKEN_OPTIMIZATION: PipelineContract(
        task=TaskKind.TOKEN_OPTIMIZATION,
        pipeline="text",
        required_capabilities=_TEXT,
        default_allow_paid=True,
        default_allow_user_pays=True,
    ),
    TaskKind.DOCUMENT_EDITING: PipelineContract(
        task=TaskKind.DOCUMENT_EDITING,
        pipeline="text",
        required_capabilities=_TEXT_REASONING,
        default_allow_paid=True,
        default_allow_user_pays=True,
    ),
    TaskKind.SITREP: PipelineContract(
        task=TaskKind.SITREP,
        pipeline="text",
        required_capabilities=_TEXT_REASONING,
        default_allow_paid=True,
        default_allow_user_pays=True,
    ),
    TaskKind.PLANNING: PipelineContract(
        task=TaskKind.PLANNING,
        pipeline="text",
        required_capabilities=_TEXT_REASONING,
        default_allow_paid=True,
        default_allow_user_pays=True,
    ),
    TaskKind.CONSENSUS: PipelineContract(
        task=TaskKind.CONSENSUS,
        pipeline="consensus",
        required_capabilities=_TEXT_REASONING,
        default_allow_paid=False,
        default_allow_user_pays=False,
        allowed_billing_classes=frozenset({BillingClass.FREE, BillingClass.FREE_QUOTA}),
        required_metadata_keys=frozenset({"consensus_preflight"}),
    ),
    TaskKind.VERIFICATION: PipelineContract(
        task=TaskKind.VERIFICATION,
        pipeline="text",
        required_capabilities=_TEXT_REASONING,
        default_allow_paid=True,
        default_allow_user_pays=True,
    ),
    TaskKind.CODING_AUX: PipelineContract(
        task=TaskKind.CODING_AUX,
        pipeline="text",
        required_capabilities=_TEXT_REASONING,
        default_allow_paid=True,
        default_allow_user_pays=True,
    ),
    TaskKind.IMAGE_GENERATION: PipelineContract(
        task=TaskKind.IMAGE_GENERATION,
        pipeline="image",
        required_capabilities=_IMAGE,
        default_allow_paid=True,
        default_allow_user_pays=False,
        required_metadata_keys=frozenset({"aspect_ratio", "output_format"}),
        forbidden_metadata_keys=frozenset({"seconds", "size"}),
    ),
    TaskKind.VIDEO_GENERATION: PipelineContract(
        task=TaskKind.VIDEO_GENERATION,
        pipeline="video",
        required_capabilities=_VIDEO,
        default_allow_paid=True,
        default_allow_user_pays=False,
        required_metadata_keys=frozenset({"seconds", "size"}),
        forbidden_metadata_keys=frozenset({"aspect_ratio", "output_format"}),
    ),
}


def contract_for_task(task: TaskKind | str) -> PipelineContract:
    parsed = parse_task_kind(task)
    return TASK_CONTRACTS[parsed]


def billing_route_intent(allow_paid: bool, allow_user_pays: bool) -> str:
    if not allow_paid and not allow_user_pays:
        return "free_only"
    if not allow_paid and allow_user_pays:
        return "free_or_user_pays"
    if allow_paid and not allow_user_pays:
        return "free_or_paid"
    return "all_billing_paths"


def route_intent(task: TaskKind | str, allow_paid: bool, allow_user_pays: bool) -> str:
    contract = contract_for_task(task)
    return f"{contract.pipeline}:{billing_route_intent(allow_paid, allow_user_pays)}"


def validate_request_contract(request: RouteRequest) -> None:
    contract = contract_for_task(request.task)
    if not contract.required_capabilities.issubset(request.required_capabilities):
        raise ValueError(
            f"{request.task.value} requires capabilities "
            f"{sorted(cap.value for cap in contract.required_capabilities)}"
        )
    metadata_keys = set(request.metadata)
    missing = contract.required_metadata_keys - metadata_keys
    if missing:
        raise ValueError(
            f"{request.task.value} requires metadata keys {sorted(missing)}"
        )
    forbidden = contract.forbidden_metadata_keys & metadata_keys
    if forbidden:
        raise ValueError(
            f"{request.task.value} does not accept metadata keys {sorted(forbidden)}"
        )
    if request.reasoning_effort is not None and request.task in {
        TaskKind.IMAGE_GENERATION,
        TaskKind.VIDEO_GENERATION,
    }:
        raise ValueError(f"{request.task.value} does not accept reasoning_effort")
    if contract.allowed_billing_classes is not None:
        route = str(request.metadata.get("route_intent") or "")
        if route == "consensus:free_only":
            return


def candidate_supported_parameters(candidate: ModelCandidate) -> set[str]:
    supported: set[str] = set()
    raw = candidate.metadata.get("raw")
    if isinstance(raw, dict):
        for key in (
            "supported_parameters",
            "supportedParameters",
            "supported_request_parameters",
            "supportedRequestParameters",
        ):
            value = raw.get(key)
            if isinstance(value, (list, tuple, set)):
                supported.update(str(item) for item in value)
    supported.update(str(item) for item in candidate.supported_parameters)
    return supported
