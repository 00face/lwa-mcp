from pathlib import Path

def test_release_check_is_present_and_non_promoting():
    script = Path("scripts/lwa-release-check").read_text(encoding="utf-8")
    assert "pytest" in script
    assert "compileall" in script
    assert "diff" in script
    assert "github" not in script.lower()
