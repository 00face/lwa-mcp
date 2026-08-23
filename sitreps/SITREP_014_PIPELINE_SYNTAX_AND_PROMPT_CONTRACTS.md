# SITREP 014 — Pipeline Syntax and Prompt-Variable Contracts Rite

**Date:** 2026-08-02  
**Status:** Complete; contract, lifecycle, and offline regression gates are green  
**Related work order:** [WO-016](../workorders/WO-016-pipeline-syntax-and-prompt-contracts.md)

## Situation

Recent Lwa connectivity validation first failed at request validation, not at a
provider: a prose task label was supplied where `TaskKind` is required, then
`low` was supplied where the quality enum permits only `economy`, `balanced`,
or `high`. A corrected `query` / `economy` request completed through the
preflight-locked ZAI route. This proves the immediate failure class is a
surface-contract gap.

The same gap exists for prompt templates. A public library recipe replaces
`{input}` with the operator input. Consensus separately reserves
`{{CONSENSUS_TRANSCRIPT}}` for an internally locked synthesis prompt. Without
a clear validator and documentation, a caller can confuse these grammars or
choose a generic pipeline for a specialized task.

## Task rite

1. Snapshot the current public `TaskKind`, quality, MCP, CLI, and template
   contracts without reading credentials or provider secrets.
2. Add one canonical contract and route all boundary validation through it.
3. Exercise every task and quality value offline, including invalid examples.
4. Exercise public recipe placeholders separately from internal consensus
   synthesis placeholders.
5. Confirm an invalid request produces no ready plan, no provider invocation,
   and no Working state.
6. Publish matching operator and library documentation, then record the exact
   test commands and results in a closing SITREP.

## Required syntax

| Field | Public contract |
|---|---|
| `task` | One exact `TaskKind` value; labels and prose are not accepted. |
| `quality` | `economy`, `balanced`, or `high`. |
| Generic recipe variable | `{input}` only. |
| Consensus synthesis variable | `{{CONSENSUS_TRANSCRIPT}}`, internal only. |
| Execution lifecycle | validate → preflight/lock → confirmation when required → Working → single-use execution. |

## Gates

- **G1 — deterministic validation:** unknown enums and placeholders fail
  locally with a correction; no provider route is selected.
- **G2 — correct pipeline:** specialized task kinds enter their specialized
  preparation path and cannot downgrade to generic text handling.
- **G3 — prompt safety:** diagnostics identify only field/placeholder names,
  never prompt values, credentials, or plan tokens.
- **G4 — lifecycle integrity:** only a ready preflight can issue a token, and
  only one execution can consume it.
- **G5 — documentation parity:** tool schemas, CLI help, and Markdown guides
  agree with the canonical contract.

## Current result and next action

The first implementation slice is complete:

- `src/lwa_mcp/syntax.py` now owns canonical task and quality parsing,
  public `{input}` template validation, and the machine-readable contract.
- MCP, service, pipeline, library, and workflow boundaries use the parser.
- Operator and tool-library docs now publish the same accepted values.
- Focused tests passed: **51**.
- Full regression passed: **87 passed, 2 deprecation warnings**.

The corrected ZAI call remains connectivity evidence only. No provider call was
made by this rite. Invalid syntax now has lifecycle assertions proving no plan
token, route, request, Working state, or provider invocation is created. WO-016
and Rite 9 are complete; any later live smoke is a separate provider-access
rite and does not weaken these offline gates.
