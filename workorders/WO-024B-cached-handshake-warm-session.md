# WO-024B - Cached MCP Handshake and Warm Session

**Status:** Partial - cache tooling complete; live MCP startup remains blocked by timeout  
**Priority:** P0  
**Parent:** SITREP-024  
**Task rite:** [TR-024B](../task-rites/TR-024B-cached-handshake-warm-session.md)

## Objective

Reduce startup and capability-discovery overhead without weakening MCP
discoverability or the strict provider execution lifecycle.

## Scope

- Add reviewed scripts under `scripts/handshake/` for capability caching,
  smoke validation, warm-session startup, and compact reporting.
- Cache a redacted capability manifest by server/protocol/config hash.
- Keep `scripts/check-mcp-handshake.py` as the full diagnostic path.
- Fail closed on hash mismatch, missing required surface, timeout, or stale
  cache; never infer capability from an old manifest.

## Acceptance

- [ ] Cold and warm timings are recorded separately.
- [ ] Warm operation avoids repeated tool/resource/prompt discovery in a live host session.
- [x] Cache invalidates on server, protocol, config, or required-surface change.
- [x] Required tools/resources/prompts are still verified by the smoke path.
- [x] Scripts were source-reviewed before execution.

## Exit boundary

No provider completion, paid route, credential change, or global client config
rewrite is authorized.

## Evidence - 2026-08-08

- Added `scripts/handshake/` cache, smoke, report, and warm-session wrappers.
- Offline cache, invalidation, malformed-cache, and report tests pass.
- Live smoke returns explicit `mcp_handshake_timeout`; no provider call was made.
- Focused verification: `20 passed`; targeted Ruff and compilation pass.
