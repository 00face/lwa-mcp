# SITREP 012 - Model and Pipeline Call Discipline Rite

**Date:** 2026-07-25  
**Status:** Implemented in-repo; Codex plugin skills now carry the workflow  
**Related work order:** [WO-007](../workorders/WO-007-model-pipeline-call-discipline.md)

## Situation

The current repository and Codex environment can surface two distinct classes
of mismatch:

- A model may be selected with a service tier that it does not advertise.
- A pipeline may be asked to execute with request parameters or assumptions it
  cannot support.

This rite exists to make those mismatches explicit at the documentation and
test-planning layer. The repository now enforces the task/pipeline contract in
code and tests. The local Codex config was also switched to `gpt-5.6-luna`
with `priority`, which matches the advertised tier set in the cache and
removes the boot warning in this environment.

## Rite goals

1. Define the per-model matrix that governs service tiers, reasoning levels,
   and supported request parameters.
2. Define the per-pipeline matrix that governs text, consensus, image, video,
   library, and startup paths.
3. Separate route intent from route availability so `allow_paid=true` or a
   model migration alias never implies an unsupported call is acceptable.
4. Record the exact pass/fail evidence for each model and pipeline once the
   corresponding tests exist.

## Ledger prompts for the next execution

- Capture the configured model, advertised tiers, and selected route intent
  before any provider call.
- Reject unsupported service tiers and provider parameters during preflight.
- Keep startup and discovery probes separate from provider execution probes.
- Record the validated model/pipeline matrix in the coordination ledger once
  the checks are implemented.

## Acceptance gates

- [x] Every configured model has a documented, test-backed call contract.
- [x] Every pipeline has an explicit allowed-parameter list.
- [x] Route selection fails clearly instead of drifting to an unsupported
  model or tier.
- [x] The next sitrep records individual model/pipeline outcomes rather than a
  single aggregate success claim.

## Evidence

- `./.venv/bin/python -m pytest tests/test_preflight.py tests/test_model_tiers.py tests/test_router.py tests/test_providers.py -q`
- `./.venv/bin/python -m pytest tests/test_cli.py -q`
- `python3 -m compileall src/lwa_mcp`
- `./.venv/bin/lwa-router doctor --show-dashboard-url`

The focused suite passed after adding explicit route-intent metadata, contract
validation, model-tier reporting for advertised service tiers and parameters,
provider/router checks for unsupported response-format requests, and launcher
hardening for dashboard startup. Legacy repository-owned command shortcuts are
deprecated; no user-global Codex command or prompt files are installed.
