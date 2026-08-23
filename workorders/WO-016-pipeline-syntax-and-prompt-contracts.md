# WO-016 — Pipeline Syntax and Prompt-Variable Contracts

**Status:** complete — canonical contract, boundary validation, lifecycle tests, and documentation parity verified  
**Priority:** P1  
**Owner:** Lwa MCP maintainers

## Objective

Make every Lwa pipeline invocable through one canonical, discoverable contract:
valid task syntax, valid quality syntax, the correct specialized preparation
tool, and an explicit prompt-template variable vocabulary. Invalid input must
fail before route selection with a short correction that identifies the
accepted values; it must never reach a provider.

## Triggering evidence

- A connectivity smoke test used `"Provider connectivity smoke test"` as
  `task`. `prepare_task` rejected it because the field is a `TaskKind`, not a
  free-form label.
- The same test used `quality="low"`. Request validation rejected it; the
  supported values are `economy`, `balanced`, and `high`.
- The corrected request used `task="query"`, `quality="economy"`, completed
  the locked ZAI route, and demonstrated that the failure was caller syntax,
  not provider connectivity.
- Prompt recipes currently substitute `{input}` at execution. Consensus keeps
  `{{CONSENSUS_TRANSCRIPT}}` as an internal locked synthesis placeholder. The
  public and internal placeholder grammars must not be conflated.

## Scope

1. Publish a machine-readable task/quality/placeholder contract that is shared
   by MCP tool schemas, CLI choices, library validation, and operator docs.
2. Validate public task names against every `TaskKind` value:
   `quick_response`, `query`, `conversation_compression`,
   `token_optimization`, `document_editing`, `sitrep`, `planning`,
   `consensus`, `verification`, `coding_aux`, `image_generation`, and
   `video_generation`.
3. Validate quality only as `economy`, `balanced`, or `high`.
4. Make specialized pipelines explicit: consensus uses the consensus builder;
   image/video use their media preparation tools; all other text tasks use
   `prepare_task` or their matching convenience preparer.
5. Define public prompt recipes as `{input}` only. Reject missing or unknown
   variables at create/update time and again before preparation. Reserve
   `{{CONSENSUS_TRANSCRIPT}}` for the internally-generated consensus synthesis
   prompt; callers and library tools cannot supply it.
6. Preserve the existing lifecycle: validate → preflight/lock → obtain any
   required confirmation → begin Working → `run_prepared_task` once. A
   validation failure creates neither a provider call nor a plan token.

## Non-goals and safety boundary

- This order does not change routing scores, provider credentials, billing
  consent, or the selected provider/model.
- It does not expose prompt bodies, template values, tokens, or credentials in
  diagnostics.
- It does not use a provider response to validate syntax; syntax checks are
  deterministic and offline.

## Work packages

1. **Canonical contracts:** place `TaskKind`, quality values, pipeline entry
   points, and allowed placeholders in one importable contract module.
2. **Boundary validation:** have MCP, CLI, library create/update, and library
   execution use the contract and return a structured, bounded error with the
   supplied field name and accepted values.
3. **Pipeline selection:** test that consensus cannot enter generic single-route
   preparation and media cannot inherit text-only assumptions.
4. **Template safety:** parse placeholders without interpolation; require one
   or more `{input}` occurrence for public recipes, reject unknown/braced
   variants, and keep the internal consensus placeholder inaccessible.
5. **Documentation:** update the operator quick-start and tool-library guide
   with copyable canonical examples and a task-to-tool table.
6. **Evidence ledger:** record task, quality, entry point, template class,
   validation result, plan ID only after readiness, and execution outcome;
   never record secret or raw prompt content.

## Acceptance checks

- [ ] One parameterized offline test accepts every `TaskKind` at the public
      boundary and rejects an unknown value with the canonical list.
- [ ] One parameterized offline test accepts all three qualities and rejects
      `low`, `medium`, empty, and arbitrary values before routing.
- [x] Each public task maps to its correct preparation pipeline; consensus,
      image, and video cannot silently use a generic text path.
- [x] Prompt-recipe creation and execution accept `{input}` and reject missing,
      unknown, or internal-only placeholders without provider execution.
- [x] The consensus synthesis placeholder is created and filled only inside the
      locked consensus workflow.
- [x] Invalid syntax leaves the preflight ledger without a ready plan token and
      the usage ledger without a provider request.
- [x] MCP schemas, CLI help, `docs/OPERATOR_QUICKSTART.md`, and
      `docs/TOOL_LIBRARY.md` present the same accepted values and examples.
- [x] Focused offline suite and full regression suite pass.

## Rite 9 execution evidence — 2026-08-02

- Added `src/lwa_mcp/syntax.py` with canonical task, quality, and public
  template validation plus a machine-readable syntax contract.
- Wired validation into request construction, pipeline contracts, MCP task
  entry points, library recipes, script registration, and workflow patterns.
- Added 12 task/quality/placeholder regression cases and MCP contract-surface
  coverage.
- Focused suite: **51 passed** (`test_syntax_contract`, tool library, MCP
  surface, preflight, and router).
- Full suite: **87 passed, 2 deprecation warnings** in 5.58s.
- Invalid syntax was proven to leave preflight, route, and request ledgers
  empty; no provider call was made by this rite.

## Rollback

Keep validation additive and versioned. If a compatibility alias is necessary,
normalize it at the boundary, emit a deprecation warning, and test its removal
date; do not silently reinterpret arbitrary strings. Revert the contract and
documentation change together if a published client cannot migrate.

## Exit criteria

Close only when the canonical contract is implemented, every boundary shares
it, invalid requests are proven offline not to create a route or provider call,
and a follow-up SITREP separates verified behavior from any compatibility
aliases still retained.
