# WO-004: Dashboard and MCP Surface Completeness

Status: complete; dashboard/API lifecycle, redaction paths, MCP resource/prompt surface, and handshake validated
Priority: P1

## Objective

Expose accurate operational state while keeping secrets and sensitive prompt
content out of default responses.

## Scope

- Verify provider/model catalog, billing classes, quotas, caps, route locks,
  approvals, lifecycle state, usage, costs, consensus, tool-library evidence,
  and audit history.
- Validate all required MCP tools, resources, prompts, schemas, and deprecated
  aliases.
- Confirm dashboard port defaults do not conflict with Castor/Pollux and remain
  configurable.

## Acceptance checks

- [x] Dashboard/API tests assert redaction and lifecycle accuracy.
- [x] Required MCP names remain discoverable with concise descriptions.
- [x] Deprecated aliases cannot bypass strict preflight.
- [x] Dashboard metadata reports the current v0.4.1 release.
- [x] Dashboard-facing provider and execution errors use redacted messages.
