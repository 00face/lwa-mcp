"""Non-mutating GitHub promotion planning boundary."""
from __future__ import annotations

import re
from typing import Any


def promotion_plan(repository: str, source_sha: str, diff_hash: str, *, approved: bool = False) -> dict[str, Any]:
    """Return an idempotent PR plan; creation is deliberately a separate adapter."""
    if not re.fullmatch(r"[^/]+/[^/]+", repository):
        return {"ready": False, "blockers": ["repository_format_invalid"]}
    if not re.fullmatch(r"[0-9a-f]{7,64}", source_sha) or not re.fullmatch(r"[0-9a-f]{64}", diff_hash):
        return {"ready": False, "blockers": ["promotion_identity_invalid"]}
    if not approved:
        return {"ready": False, "blockers": ["approval_required"]}
    return {"schema": "lwa-github-promotion/v1", "ready": True, "repository": repository,
            "key": f"{repository}:{source_sha}:{diff_hash}", "direct_push": False, "auto_merge": False}
