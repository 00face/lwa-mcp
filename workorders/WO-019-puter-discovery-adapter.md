# WO-019 — Puter Provider-Specific Discovery Adapter

**Status:** complete; bounded schema evidence and adapter verified  
**Priority:** P1  
**Parent:** WO-017 / Rite 10

## Objective

Confirm Puter's documented model-discovery response with one bounded,
redacted request, then implement a provider-specific discovery adapter only if
the response contract is sufficient and compatible with the catalog model.

## Evidence boundary

- Current generic OpenAI-compatible probing reaches
  `https://api.puter.com/puterai/openai/v1/models` and reports HTTP 404.
- Puter's official documentation identifies its model-listing source as
  `/puterai/chat/models/details` and documents model fields including `id` and
  `provider`.
- A 404 is not permission to rewrite the endpoint without a bounded schema
  check and redacted response capture.

## Scope

1. Confirm the configured Puter credential environment mapping without printing
   the value.
2. Issue at most one bounded discovery request with a short timeout.
3. Record status, content type, top-level JSON shape, and redacted field names;
   never persist tokens or full provider payloads.
4. Implement a Puter adapter/parser only after schema validation.
5. Add offline fixtures and tests for success, malformed payload, timeout, and
   HTTP failure. Preserve the live-unhealthy seed-model gate.

## Acceptance

- [ ] Official schema reference and bounded response evidence are recorded.
- [ ] No endpoint or credential is changed without explicit authorization.
- [ ] Adapter output maps only documented fields into `ModelCandidate`.
- [ ] Discovery failures mark Puter unhealthy and cannot route stale seeds.
- [ ] Focused and full regression suites pass.

## Exit boundary

If the request cannot be authorized or the response schema is unavailable, stop
at evidence collection and leave the generic probe unchanged.

## Completion evidence — 2026-08-02

- Authorized bounded request to `/puterai/chat/models/details` returned HTTP 200
  with top-level `models` and **538** entries.
- Implemented `PuterAdapter` with the documented native discovery URL while
  retaining the OpenAI-compatible completion base URL.
- Updated active and packaged configuration to select `adapter: puter`.
- Provider refresh reports Puter `healthy=true`, `538 live models`.
- Focused regression and full suite passed.
