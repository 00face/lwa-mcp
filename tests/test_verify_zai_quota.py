import json
import subprocess
import sys
from pathlib import Path


def test_zai_quota_verifier_rejects_other_provider(tmp_path):
    snapshot = tmp_path / "quota.json"
    snapshot.write_text(
        json.dumps(
            {
                "provider": "groq",
                "account_scope": "acct",
                "available_tokens": 1_000_000,
                "unit": "tokens",
                "captured_at": "2026-08-08T11:30:00+00:00",
                "reset_at": "2026-08-09T00:00:00+00:00",
                "source": "provider_header",
                "authoritative": True,
            }
        ),
        encoding="utf-8",
    )
    script = Path("scripts/verify_zai_quota.py")
    result = subprocess.run(
        [sys.executable, str(script), str(snapshot), "--account-scope", "acct", "--control-plane-tokens", "186", "--now", "2026-08-08T12:00:00+00:00"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "provider_must_be_zai" in result.stdout
