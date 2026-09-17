from pathlib import Path

from lwa_mcp.config import LoadedConfig, RouterSettings
from lwa_mcp.db import UsageDB
from lwa_mcp.models import LibraryToolStatus, TaskKind
from lwa_mcp.patterns import PatternDetector
from lwa_mcp.syntax import validate_public_prompt_template
from lwa_mcp.tool_library import ToolLibrary


def make_config(tmp_path: Path) -> LoadedConfig:
    settings = RouterSettings(
        providers={},
        models=[],
        pattern_min_occurrences=3,
        auto_create_library_tools=True,
        auto_activate_prompt_tools=True,
    )
    return LoadedConfig(
        settings=settings,
        config_path=tmp_path / "router.yaml",
        env_path=tmp_path / "lwa.env",
        db_path=tmp_path / "lwa.sqlite3",
        tool_library_path=tmp_path / "tool-library",
    )


def test_repeated_workflow_creates_documented_tool(tmp_path):
    cfg = make_config(tmp_path)
    db = UsageDB(cfg.db_path)
    library = ToolLibrary(cfg.tool_library_path)
    detector = PatternDetector(cfg, db, library)

    result = None
    for _ in range(3):
        result = detector.observe(
            task=TaskKind.DOCUMENT_EDITING,
            sample="Normalize CSS glass controls and preserve file paths.",
            workflow_name="Normalize liquid glass controls",
            description="Normalize repeated liquid-glass CSS controls while preserving project literals.",
            project="UI studies",
            success=True,
            tags=["css", "glass"],
        )

    assert result is not None
    assert result["created_tool"] is not None
    slug = result["created_tool"]["slug"]
    tool = library.get(slug)
    assert tool.status == LibraryToolStatus.ACTIVE
    assert tool.evidence_count == 3
    directory = cfg.tool_library_path / "tools" / slug
    assert (directory / "README.md").exists()
    assert (directory / "tool.yaml").exists()
    assert (directory / "run.py").exists()
    assert slug in (cfg.tool_library_path / "CATALOG.md").read_text(encoding="utf-8")
    assert library.search("liquid glass css", task=TaskKind.DOCUMENT_EDITING)[0]["slug"] == slug

    detector.observe(
        task=TaskKind.DOCUMENT_EDITING,
        sample="Normalize CSS glass controls and preserve file paths.",
        workflow_name="Normalize liquid glass controls",
        description="Normalize repeated liquid-glass CSS controls while preserving project literals.",
        project="UI studies",
        success=True,
    )
    assert library.get(slug).evidence_count == 4


def test_script_tool_is_review_gated(tmp_path):
    library = ToolLibrary(tmp_path / "tool-library")
    tool = library.register_script(
        name="Example script",
        description="A review-gated example.",
        task=TaskKind.CODING_AUX,
        source='print("ok")\n',
    )
    assert tool.status == LibraryToolStatus.DRAFT
    assert tool.approved is False


def test_prompt_tool_manifest_includes_review_metadata(tmp_path):
    library = ToolLibrary(tmp_path / "tool-library")
    tool = library.create_prompt_tool(
        name="Example prompt tool",
        description="A reusable prompt recipe.",
        task=TaskKind.QUERY,
        prompt_template="Answer {input}",
        activate=False,
        metadata={"source": "test"},
    )
    bundle = library.read_bundle(tool.slug)
    manifest = bundle["manifest"]
    assert manifest["origin"] == "operator"
    assert manifest["review_state"] == "draft"
    assert manifest["safety_state"] == "safe"


def test_prompt_template_contract_accepts_input_only(tmp_path):
    library = ToolLibrary(tmp_path / "tool-library")
    tool = library.create_prompt_tool(
        name="Input recipe",
        description="A valid recipe.",
        task="query",
        prompt_template="Answer this: {input}",
    )
    assert tool.prompt_template == "Answer this: {input}"


def test_prompt_template_contract_rejects_unknown_and_internal_variables(tmp_path):
    library = ToolLibrary(tmp_path / "tool-library")
    for template in ("Answer {question}", "Answer {{CONSENSUS_TRANSCRIPT}}", "No variables"):
        try:
            library.create_prompt_tool(
                name="Invalid recipe",
                description="Invalid.",
                task="query",
                prompt_template=template,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid template: {template}")


def test_public_template_validator_rejects_malformed_braces():
    for template in ("{input", "input}", "{input} and {other}"):
        try:
            validate_public_prompt_template(template)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted malformed template: {template}")
