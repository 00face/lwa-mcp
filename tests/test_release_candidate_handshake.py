def test_release_candidate_handshake_is_non_mutating():
    from pathlib import Path
    import runpy
    namespace = runpy.run_path(str(Path("scripts/handshake/release_candidate_handshake.py")))
    result = namespace["run"](Path.cwd())
    assert result["mutated"] is False
    assert ".env" not in result["stage"]
