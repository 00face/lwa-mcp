# SITREP 010 — Agouti Integration Failure and Inoculation

**Date:** 2026-07-25  
**Status:** Failed exercise; remediation work order open  
**Related work order:** [WO-006](../workorders/WO-006-integration-failure-inoculation.md)

**Remediation update:** Consensus voter policy is now fixed and covered by
regression tests; the SITREP remains failed overall until the remaining gates
are completed.

## Situation

An end-to-end Lwa exercise was requested to obtain consensus guidance, make a
free-route fallback, make one final pro coding call, and then build an
isometric cat-emoji Game of Life app. The exercise did not achieve the full
requested routing outcome. Groq completed a free-quota advisory; the consensus
run and final pro call did not complete successfully.

## Timeline and outcome

1. `suggest_library_tools` rejected two invalid task strings. Inspection of the
   repository's `TaskKind` enum identified `coding_aux` and
   `document_editing` as valid values.
2. A generic `prepare_task` call selected a single paid route, which did not
   satisfy the requested consensus shape.
3. `build_consensus` was then used. Its no-paid preflight still displayed a
   Puter `user_pays` voter, leaving the billing policy ambiguous or violated.
4. The locked consensus execution stopped with `repreflight_required` because
   Puter rejected the unsupported `temperature` parameter. This was a correct
   stop under the strict no-dynamic-rerouting doctrine.
5. A later ready fallback token was rejected as expired/used, so another
   preflight was required. The token was not reused.
6. A fresh Groq `free_quota` query preflight and execution completed and
   returned implementation guidance.
7. The final pro preflight selected ZenMux/Gemini and was approved, but
   execution returned HTTP 403 `access_denied`. No pro result was received.
8. The requested absolute directory `/code/agouti_simulator` was absent. The
   app was created at the workspace-relative path
   `code/agouti_simulator/` instead.
9. JavaScript syntax verification passed. Browser-level runtime verification
   was not run.

## Impact

- No valid multi-model consensus result was produced.
- The requested pro coding handoff was attempted but not completed.
- The app exists and is locally inspectable, but its requested path contract
  was not satisfied.
- Runtime behavior remains less verified than the implementation status
  implied.

## What worked

- Lwa preflight locks exposed provider, model, billing class, budget, and
  lifecycle state before execution.
- Provider failures stopped the active Working phase and returned
  `repreflight_required` instead of silently switching models.
- The fresh Groq free-quota route completed.
- The app was created with the requested isometric and cat-emoji concepts.
- `node --check` passed for `app.js`.

## Remediation evidence

- `prepare_consensus` now selects every eligible free/free-quota provider rather
  than truncating to `max_parallel_consensus`.
- Consensus voters explicitly disable user-pays routes.
- A policy assertion rejects any non-free voter before a consensus plan is
  created.
- Full Python suite: **48 passed**, with 2 existing FastAPI deprecation
  warnings.

Still untested: browser-level Agouti runtime behavior, absolute target-path
handling, token lifecycle correlation, and a successful pro-provider call.

## Inoculation decision

The system must treat routing intent, billing policy, provider capabilities,
token state, filesystem target, and browser verification as separate gates.
Passing one gate must never be reported as passing the whole exercise. In
particular:

- A synthesis route is not consensus unless the preflight says
  `mode=consensus` and execution returns a result.
- A preflight approval is not a successful provider call.
- A free fallback is not permission to make an unrequested paid call.
- A path fallback is not equivalent to the requested absolute path.
- Syntax validity is not browser runtime validity.

## Required next steps

Execute WO-006 acceptance tests, then produce SITREP 011 with explicit
`fixed`, `still failing`, and `untested` sections. Do not mark this exercise
ready until the consensus and browser gates have actual successful evidence.
