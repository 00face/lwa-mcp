import importlib.util
import json
from pathlib import Path

from lwa_mcp.benchmark import GOLDEN_CASES, run_benchmark


def test_benchmark_is_provider_free_and_reproducible():
    first = run_benchmark(quota_tokens=1_000_000)
    second = run_benchmark(quota_tokens=1_000_000)

    assert first == second
    assert len(first["cases"]) == 7
    assert first["reproducibility"] == {"runs": 2, "identical_case_order": True, "provider_calls": 0}
    assert first["gates"]["no_duplicate_provider_execution"] is True


def test_benchmark_preserves_quality_and_measures_compact_savings():
    result = run_benchmark()

    assert result["quality"]["baseline_pass_rate"] == 1.0
    assert result["quality"]["compact_pass_rate"] == 1.0
    assert result["quality"]["regression_gate_pass"] is True
    assert result["efficiency"]["compact_bytes"] < result["efficiency"]["standard_bytes"]
    assert result["efficiency"]["compact_estimated_tokens"] < result["efficiency"]["standard_estimated_tokens"]
    assert result["denominators"]["quota_overhead_percent"] is None
    assert result["gates"]["10_of_10_blocked_by_unreported_or_live_evidence"] is True


def test_benchmark_cli_output_is_json(monkeypatch, capsys):
    path = Path("scripts/benchmark_quality_tokens.py")
    spec = importlib.util.spec_from_file_location("benchmark_quality_tokens", path)
    assert spec and spec.loader
    benchmark_quality_tokens = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(benchmark_quality_tokens)

    monkeypatch.setattr("sys.argv", ["benchmark_quality_tokens", "--quota-tokens", "1000000"])
    benchmark_quality_tokens.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["denominators"]["quota_tokens"] == 1_000_000
    assert payload["mode"] == "offline_mock"


def test_golden_cases_have_required_quality_contracts():
    assert {case.name for case in GOLDEN_CASES} == {
        "query",
        "document-edit",
        "coding",
        "verification",
        "sitrep",
        "failure-recovery",
        "consensus",
    }
    assert all(case.required_fields and case.required_literals for case in GOLDEN_CASES)
