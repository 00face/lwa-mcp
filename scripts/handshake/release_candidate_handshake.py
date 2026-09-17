#!/usr/bin/env python3
"""Plan a selective release candidate without mutating the worktree."""
from __future__ import annotations
import json
import argparse
import subprocess
from pathlib import Path

ALLOW_EXACT = {
    "Containerfile.sandbox", "docs/REPRODUCIBLE_RELEASE.md", "scripts/lwa-release-check",
    "scripts/handshake/release_candidate_handshake.py",
    "src/lwa_mcp/evidence.py", "src/lwa_mcp/github_promotion.py", "src/lwa_mcp/image_attestation.py",
    "src/lwa_mcp/image_gate.py", "src/lwa_mcp/local_evidence.py", "src/lwa_mcp/policy_bootstrap.py",
    "src/lwa_mcp/rite_pipeline.py", "src/lwa_mcp/sandbox_executor.py", "src/lwa_mcp/sandbox_policy.py",
    "src/lwa_mcp/signer_policy.py", "tests/test_credentials.py", "tests/test_evidence.py",
    "tests/test_github_promotion.py", "tests/test_image_attestation.py", "tests/test_image_gate.py",
    "tests/test_local_evidence.py", "tests/test_policy_bootstrap.py", "tests/test_release_check.py",
    "tests/test_release_candidate_handshake.py", "tests/test_rite_pipeline.py", "tests/test_sandbox_executor.py",
}

def run(root: Path, *, apply: bool = False) -> dict[str, object]:
    raw = subprocess.run(["git", "status", "--short"], cwd=root, text=True, capture_output=True, check=True).stdout.splitlines()
    paths = [line[3:] for line in raw if len(line) >= 4]
    candidate = sorted(path for path in paths if path in ALLOW_EXACT)
    unrelated = sorted(set(paths) - set(candidate))
    if apply:
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
        if branch != "chore/lwa-assurance-release":
            subprocess.run(["git", "switch", "-c", "chore/lwa-assurance-release"], cwd=root, check=True)
        subprocess.run(["git", "add", "--", *candidate], cwd=root, check=True)
    return {"schema": "lwa-release-candidate/v1", "mutated": apply,
            "branch_action": "git switch -c chore/lwa-assurance-release",
            "stage": candidate, "unrelated": unrelated,
            "ready_for_review": bool(candidate) and not any(path == ".env" for path in candidate)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(Path(__file__).resolve().parents[2], apply=args.apply), indent=2))
