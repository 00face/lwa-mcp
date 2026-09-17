def test_evidence_requires_same_image_and_all_hashes():
    from lwa_mcp.evidence import validate_evidence
    image = "registry.test/lwa@sha256:" + "a" * 64
    item = {"sha256": "b" * 64}
    record = {"image": image, "attestation": item, "sbom": item, "vulnerabilities": item, "runtime": item}
    assert validate_evidence(record, image)["valid"] is True
    assert validate_evidence({"image": image}, image)["valid"] is False
    assert validate_evidence(record, image.replace("a", "c"))["blockers"] == ["evidence_digest_mismatch"]

def test_evidence_write_is_bounded_and_private(tmp_path):
    from lwa_mcp.evidence import write_evidence
    target = tmp_path / "evidence.json"
    write_evidence(target, {"image": "x", "runtime": {"sha256": "a"}})
    assert target.stat().st_mode & 0o777 == 0o600

def test_evidence_record_hashes_all_artifacts(tmp_path):
    from lwa_mcp.evidence import evidence_record, validate_evidence
    paths = {}
    for name in ("attestation", "sbom", "vulnerabilities", "runtime"):
        path = tmp_path / name
        path.write_text(name, encoding="utf-8")
        paths[name] = path
    image = "registry.test/lwa@sha256:" + "a" * 64
    record = evidence_record(image, **paths)
    assert validate_evidence(record, image)["valid"] is True
