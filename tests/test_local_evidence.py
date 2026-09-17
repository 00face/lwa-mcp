import subprocess

def test_collect_local_evidence_writes_digest_bound_manifest(tmp_path):
    from lwa_mcp.local_evidence import collect_local_evidence
    def runner(command, **_):
        stdout = '{"distro":{"name":"Minimus","eol":false},"matches":[]}' if command[0] == "grype" else "{}"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")
    image = "registry.test/lwa@sha256:" + "a" * 64
    record = collect_local_evidence(image, tmp_path, cosign_args=["cosign"], runtime_probe=lambda: {"rootless": True}, runner=runner)
    assert record["image"] == image
    assert (tmp_path / "evidence.json").stat().st_mode & 0o777 == 0o600
