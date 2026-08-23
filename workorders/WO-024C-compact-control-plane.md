# WO-024C - Compact Control-Plane Responses

**Status:** Partial — compact transport and duplicate suggestion removal are implemented; manifest-delta/catalog-cache work remains for WO-024D follow-through.  
**Priority:** P0  
**Parent:** SITREP-024  
**Task rite:** [TR-024C](../task-rites/TR-024C-compact-control-plane.md)

## Objective

Reduce MCP/plugin bytes and repeated work while preserving semantic fields,
auditability, quality, and all safety constraints.

## Scope

- Add `compact`, `standard`, and `debug` response detail modes.
- Make compact JSON the machine-to-machine default; retain full debug output
  for failures and explicit audits.
- Remove pretty-printing from transport responses without removing fields.
- Evaluate library suggestions only for explicit discovery or recurring tasks,
  not automatically in both preflight and completion.
- Add manifest/hash deltas and bounded catalog caching.

## Acceptance

- [x] Compact, standard, and debug modes are schema-equivalent.
- [x] Required fields, prompt hashes, consent state, route locks, and errors stay
  available.
- [x] Duplicate suggestion evaluation is absent from one lifecycle.
- [x] The response-mode regression fixture preserves nested fields and literals.
- [x] Compact and standard byte lengths are measured in automated tests.

## Evidence

- 2026-08-08: `_json` is the default encoder for MCP resources and tools;
  compact mode removes whitespace while standard/debug remain available.
- 2026-08-08: `96 passed` on the full suite before the known Firefox screenshot
  environment failures; targeted Ruff and Python compilation passed.
- 2026-08-08: lifecycle regression confirms one library-suggestion evaluation
  and no duplicate suggestion payload in execution results.

## Exit boundary

Do not lower quality tiers or output budgets below measured safe limits to claim
efficiency.
