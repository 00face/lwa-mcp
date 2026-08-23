# SITREP 013 — Provider Access and Pro-Route Readiness Rite

**Date:** 2026-07-25  
**Status:** Planned; evidence captured, implementation not claimed  
**Related work order:** [WO-014](../workorders/WO-014-cross-project-provider-access.md)

## Situation

The MSF tree does not contain dedicated Codex/Lwa logs. Its checked-in
integration instructions require `GEMINI_API_KEY` in `.env.local` and declare
server-side Gemini capability. Lwa records show the operational gap: bounded
credential discovery means one project's key is not automatically a key for
every Codex project.

The same evidence says Codex OAuth session material cannot be reused as a
provider API key; Gemini/OpenAI support is present but live access is not
proven; and `allow_paid=true` can currently select a free-quota route. A
Gemini/ZenMux `403` and OpenRouter `401` are access failures, not evidence that
the requested pro route is available.

## Task rite

1. Inventory Codex project/MCP environment mappings without printing values.
2. Define and test explicit shared-vs-project credential precedence.
3. Add provider-specific OpenAI and Gemini readiness diagnostics.
4. Enforce required billing class for requests that explicitly require Pro.
5. Update MSF onboarding and Lwa operator docs to describe the boundary.
6. Run offline regression tests, then request separate operator approval for
   any live or paid provider check.

## Gates

- **Gate A — discovery:** no secret values, OAuth session data, or recursive
  home-directory scan appears in output.
- **Gate B — configuration:** shared access is opt-in, atomic, reversible, and
  preserves unrelated environment entries.
- **Gate C — routing:** a required paid/pro route fails clearly when absent;
  free fallback is allowed only when the request permits it.
- **Gate D — live verification:** ChatGPT/OpenAI and Gemini Pro claims require
  fresh provider-specific evidence and operator approval.

## Current result

No credentials were read or changed. No provider access was claimed. The next
execution should implement WO-014 and record each provider/project outcome in
the evidence ledger.
