# WO-023 — First-Response Timing and Durable MCP Attribution

**Status:** partial; readiness evidence captured, first-response probe authorized but not yet executed  
**Priority:** P1  
**Parent:** WO-022 / WO-005 / TR-007

**Design baseline:** [`/home/face/.codex/quirks/quirk_tui_plugin_design.md`]

## Objective

Measure native TUI process start, MCP readiness, prompt readiness, and first
response separately, while durably attributing startup time and failures to
individual MCP servers.

## Scope

1. Use ephemeral CLI overrides or reversible profiles only.
2. Capture monotonic timestamps for process launch, each MCP start/ready/fail
   event, prompt availability, submitted probe, first response, and shutdown.
3. Compare Lwa-enabled and Lwa-disabled profiles.
4. Persist only redacted phase metadata; never persist prompt text, credentials,
   tokens, or provider payloads.
5. Treat first-response submission as an explicit paid/external-use switch;
   without that switch, record a blocker after prompt readiness.

## Acceptance

- [ ] A timing record identifies each MCP server and phase outcome.
- [ ] Prompt readiness is measured independently from first response.
- [ ] First-response timing is recorded only after explicit authorization.
- [ ] Lwa-enabled/disabled comparison does not mutate global configuration.
- [ ] Any timeout or host blocker is durable and reproducible.

## Safe boundary

No provider completion, paid route, user-pays route, credential change, or
global MCP registration change is implied by this work order.

## Bounded evidence — 2026-08-02

- Native TUI reached the prompt in both direct and ephemeral comparison runs.
- MCP progress displayed `codex-skill-switchboard`, `codex_apps`, and `lwa`.
- One bounded run showed MCP startup interruption; a second reached the prompt
  without a warning banner.
- First-response measurement was not attempted because no explicit external
  response probe switch was enabled.

## Operator directive — 2026-08-08

- Proceed with the trivial first-response probe when the host session is
  available, keeping the probe non-sensitive and explicitly scoped to this work
  order.
