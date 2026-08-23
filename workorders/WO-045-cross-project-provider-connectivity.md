# WO-045 — Cross-project provider connectivity and runtime boundary

**Status:** QUEUED  
**Priority:** P0  
**Parent:** WO-014, WO-022, WO-036, WO-044  
**Task rite:** [TR-045](../task-rites/TR-045-cross-project-provider-connectivity.md)

## Objective

Provide one reusable, secret-safe diagnostic contract that works from the LWA
repository and every registered project. It must identify whether a failure is
caused by project registration, process configuration, restricted DNS/egress,
MCP startup, dashboard lifecycle, provider authentication, model discovery,
quota, or prompt execution.

## Current evidence

- A restricted execution environment could not resolve any provider host and
  timed out during live discovery.
- The host-level run reached the provider endpoints, refreshed 1,679 live
  models, and reported all enabled providers healthy except intentionally
  disabled SiliconFlow.
- The host-level MCP handshake passed with 40 tools, 3 resources, and 1 prompt.
- The dashboard launch log shows startup, but the process was not persistent.

These are separate gates and must remain separate in future evidence.

## Work packages

1. **Runtime manifest:** expose absolute LWA root, launcher, config path, env
   path metadata, project root, and execution-boundary classification.
2. **Connectivity classifier:** test DNS/HTTPS only from the selected execution
   boundary and classify restricted egress before provider errors are inferred.
3. **Control-plane gate:** run the stdio handshake independently of dashboard
   startup and preserve protocol/tool/resource/prompt counts.
4. **Provider metadata gate:** run the existing zero-completion live catalog
   probe and emit a bounded per-provider result with redaction.
5. **Cross-project registration:** validate that each project points to the
   same MCP command and does not require copied secrets.
6. **Operator recovery:** provide exact next actions for missing credentials,
   restricted egress, stale dashboard, failed handshake, auth denial, quota,
   and model incompatibility.

## Acceptance criteria

- The same rite passes from at least two project roots and names both roots.
- A sandbox DNS failure cannot be reported as a provider outage.
- Metadata success cannot be reported as completion success.
- Dashboard failure cannot be reported as MCP failure.
- No artifact contains API keys, OAuth tokens, authorization headers, or raw
  prompt bodies.
- SiliconFlow or another intentionally disabled provider remains visibly
  disabled and does not contaminate healthy-provider counts.
- Failures are deterministic, bounded, and nonzero where the gate is required.

## Rollback

Quarantine only the failing project registration or provider probe. Do not weaken
the common classifier, copy secrets into a project, or mark a restricted run as
healthy. Restore the last known-safe launcher/configuration metadata only.

## Exit criteria

Close when the matrix passes from LWA plus two independent projects, the MCP
handshake and catalog gates are independently green, and all remaining failures
have typed recovery instructions.

