# SITREP 001 - v0.4.1 Release Baseline

**Date:** 2026-07-24  
**Status:** P0 release baseline complete; P1 audits in progress

## Completed in this increment

- Canonicalized consent mode documentation and UI values to `always_ask`,
  `paid_only`, and `automatic` while preserving `always` and `never` input
  aliases.
- Added explicit origin, review-state, and safety-state metadata to reusable
  tool manifests and README files.
- Added focused tests for consent aliases, tool manifest metadata, approval
  token replay rejection, and expired approval rejection.
- Created prioritized work orders WO-001 through WO-005 and release battleplan
  BP-001.
- Began WO-003 and WO-004: centralized provider-error redaction, bounded
  reviewed-script output, entrypoint validation, and dashboard version alignment.
- Began WO-002: explicit unsupported-streaming behavior, route size limits,
  optional balance probe contract, and offline provider adapter tests.

## Verification evidence

- Python bytecode compilation: PASS (`python3 -m py_compile ...`).
- Security/static regression additions compile successfully, including provider
  error redaction coverage.
- Full pytest suite: NOT RUN; `pytest` is not installed in the current
  interpreter.
- Ruff: NOT RUN; `ruff` is not installed in the current interpreter.
- Runtime/import tests: NOT RUN; declared runtime dependencies including
  Pydantic, FastAPI, MCP, HTTPX, and python-dotenv were initially unavailable
  in the base interpreter; isolated verification dependencies were subsequently
  staged under `/tmp`.
- Full offline pytest suite: PASS, 21 tests.
- Ruff: PASS.
- Dashboard fresh-home import: PASS.
- Clean-wheel config/dashboard smoke: PASS.
- Provider contract/matrix tests: PASS, including mocked HTTP only.
- Existing `dist/lwa_mcp-0.4.0-py3-none-any.whl`: stale relative to source and
  not treated as a v0.4.1 release artifact.

## Open work

- Execute WO-001 in a dependency-complete environment, including clean-home
  installation and artifact verification. Completed in this rite.
- Complete provider contract audit, security/storage audit, dashboard/MCP
  surface audit, and documentation reconciliation under WO-002 through WO-005.
- Do not claim live provider, quota, balance, price, or model freshness without
  official endpoint evidence.
