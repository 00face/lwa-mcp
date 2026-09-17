import pytest

from lwa_mcp.contracts import TASK_CONTRACTS
from lwa_mcp.models import TaskKind
from lwa_mcp.syntax import (
    QUALITY_VALUES,
    REASONING_EFFORT_VALUES,
    api_reasoning_effort,
    parse_task_kind,
    syntax_contract,
    validate_quality,
    validate_reasoning_effort,
)


def test_contract_lists_every_task_and_quality():
    contract = syntax_contract()
    assert contract["tasks"] == [item.value for item in TaskKind]
    assert tuple(contract["qualities"]) == QUALITY_VALUES
    assert tuple(contract["reasoning_efforts"]) == REASONING_EFFORT_VALUES
    assert contract["reasoning_effort_mapping"] == {
        "instant": "none",
        "medium": "medium",
        "high": "high",
    }


@pytest.mark.parametrize("effort", REASONING_EFFORT_VALUES)
def test_every_reasoning_effort_is_accepted(effort):
    assert validate_reasoning_effort(effort) == effort


def test_instant_maps_to_deterministic_no_reasoning_wire_value():
    assert api_reasoning_effort("instant") == "none"


def test_unknown_reasoning_effort_reports_canonical_values():
    with pytest.raises(ValueError, match="Invalid reasoning_effort") as error:
        validate_reasoning_effort("auto")
    assert "instant" in str(error.value)


@pytest.mark.parametrize("task", [item.value for item in TaskKind])
def test_every_task_kind_is_accepted(task):
    assert parse_task_kind(task).value == task


@pytest.mark.parametrize("quality", QUALITY_VALUES)
def test_every_quality_is_accepted(quality):
    assert validate_quality(quality) == quality


@pytest.mark.parametrize("task", ["Provider connectivity smoke test", "", "QUERY"])
def test_unknown_task_reports_canonical_values(task):
    with pytest.raises(ValueError, match="Invalid task") as error:
        parse_task_kind(task)
    assert "query" in str(error.value)


@pytest.mark.parametrize("quality", ["low", "medium", ""])
def test_unknown_quality_reports_canonical_values(quality):
    with pytest.raises(ValueError, match="Invalid quality") as error:
        validate_quality(quality)
    assert "economy" in str(error.value)


def test_every_task_has_an_explicit_pipeline_contract():
    assert set(TASK_CONTRACTS) == set(TaskKind)
    assert TASK_CONTRACTS[TaskKind.CONSENSUS].pipeline == "consensus"
    assert TASK_CONTRACTS[TaskKind.IMAGE_GENERATION].pipeline == "image"
    assert TASK_CONTRACTS[TaskKind.VIDEO_GENERATION].pipeline == "video"
    assert all(
        contract.pipeline == "text"
        for task, contract in TASK_CONTRACTS.items()
        if task not in {TaskKind.CONSENSUS, TaskKind.IMAGE_GENERATION, TaskKind.VIDEO_GENERATION}
    )
