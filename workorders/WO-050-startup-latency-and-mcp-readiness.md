# WO-050 — Startup Latency and MCP Readiness

**Status:** Complete. The MCP stdio handshake and static dashboard surfaces
start before router/catalog warmup; first router-backed operations remain lazy
and local.
**Latest evidence (2026-08-21):** Handshake ordering, static-route laziness,
explicit-config fallback, focused tests, lint, live route checks, and the first
router-backed status call pass. See [WO-050 evidence](../reports/WO-050-startup-evidence.md).
**Priority:** P0
**Parent:** WO-048, WO-049
**Task rite:** [TR-050](../task-rites/TR-050-startup-latency-and-mcp-readiness.md)

## Objective

Remove the appearance of Lwa hanging during startup on low-resource systems.
The `lwa-mcp` process must begin its MCP handshake promptly, while `lwa-web`
must serve `/` and `/codex` without waiting for the persistent tool catalog or
router service to initialize.

## Contract

- `lwa-mcp` starts the stdio transport before optional local catalog warming.
- Dashboard import and static route serving do not construct `RouterService`.
- The first router-backed API/tool operation constructs the service lazily.
- No provider network call is introduced into startup.
- Startup failures remain visible through the affected operation rather than
  becoming a silent background hang.
- Existing dashboard, MCP, and work-order functionality remains additive.

## Required Work

1. Measure import, service construction, dashboard readiness, and MCP
   handshake latency on the target Linux Mint host.
2. Remove eager service construction from the MCP and static dashboard paths.
3. Add regression tests proving handshake ordering and static-route laziness.
4. Re-run focused and full verification, recording unrelated environment
   failures separately from startup regressions.

## Acceptance

- MCP handshake completes without waiting for `RouterService.initialize()`.
- `/codex` can be served before the router service is constructed.
- First router-backed operation still returns the same contract and redaction
  behavior.
- No new orphan process or provider request is created by the optimization.
- Focused tests and launcher checks pass on the constrained Linux host.

## Evidence

Store redacted measurements under `reports/WO-050-*`. Do not record prompts,
credentials, authorization headers, process environment values, or session
tokens.

## Rollback

Restore eager initialization only if a lifecycle regression is demonstrated;
retain the route and handshake tests and preserve the previous direct launcher
behavior.
