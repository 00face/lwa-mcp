# WO-046 — Cross-project prompt parity and varied task execution

**Status:** QUEUED  
**Priority:** P0  
**Parent:** WO-045, WO-016, WO-036  
**Task rite:** [TR-046](../task-rites/TR-046-cross-project-prompt-parity.md)

## Objective

Prove that projects using the shared LWA MCP surface can prepare and, when
authorized, execute varied prompt shapes with honest lifecycle and provenance
reporting. The goal is contract parity, not identical provider wording.

## Prompt classes

Cover every public text task kind: `quick_response`, `query`,
`conversation_compression`, `token_optimization`, `document_editing`, `sitrep`,
`planning`, `verification`, and `coding_aux`. Include prepare-only checks for
`consensus`, `image_generation`, and `video_generation`; execute those only
with the appropriate explicit capability and billing authorization.

## Required assertions

- `prepare_task` locks task, prompt, route, model, billing class, token budget,
  and plan lifecycle before provider work.
- `working_may_begin` is honored; no completion occurs during preparation.
- `run_prepared_task` uses the single locked plan and reports actual provider,
  model, billing class, usage, and response provenance.
- A provider failure returns a bounded failure/re-preflight instruction and does
  not silently reroute mid-work.
- Structured-output requests are rejected before execution when unsupported.
- Prompt bodies and credentials are absent from telemetry and evidence unless a
  project explicitly stores a reviewed fixture.
- The same contract holds from at least two project roots.

## Prompt quality boundary

Assertions should check required facts, lifecycle, schema, and provenance. They
must not require exact prose across providers. Deterministic prompts may require
an exact short token such as `READY`; open-ended prompts should use structural
checks.

## Acceptance

- All public text task kinds pass prepare-only coverage.
- At least one approved free/free-quota prompt from each of two project roots
  completes with accurate provider/model evidence.
- One structured-output request passes or fails before execution for a stated
  capability reason.
- One provider failure is captured without hidden fallback.
- Consensus/media paths remain gated and do not spend quota accidentally.

## Rollback

Disable only the failing prompt class or provider-specific fixture. Preserve the
common lifecycle contract and do not lower assertions to match an implementation
that violates provenance or billing policy.

