# Test Cases

## Configuration

- Fresh initialization creates config, key file, database parent, and tool-library layout.
- Key-file permissions are `0600`.
- Packaged defaults work outside the source tree.
- Missing keys exclude providers without crashing startup.

## Routing and consent

- Economy tasks prefer a suitable free/free-quota candidate.
- High-quality coding support may choose a premium specialist when allowed.
- Paid and user-pays exclusions are enforced.
- Missing capabilities, insufficient context, and exhausted caps remove candidates.
- Consent modes accept `always_ask`, `paid_only`, and `automatic` plus legacy `always` and `never` aliases.
- Confirmation tokens are single-use and expiring.
- Paid fallback after free-provider failure pauses for new consent.
- Failover never exceeds four provider attempts.

## Ledger

- Success records provider, model, task, tokens, cost, latency, and status.
- Failure records the attempted route and sanitized error.
- Prompt bodies are absent; only hashes are stored.
- Rate/quota headers create provider snapshots.

## Pattern detection

- Similar named workflow observations bind to one stable signature.
- Failed observations do not satisfy the successful-evidence threshold.
- Three successful observations create one tool under default settings.
- Re-analysis does not duplicate a pattern-bound tool.
- Generated confidence and evidence count remain visible.
- Library-tool execution is excluded from recursive pattern creation.

## Tool library

- Initialization creates `README.md`, `CATALOG.md`, `registry.json`, and `tools/`.
- Generated prompt tools contain `tool.yaml`, `README.md`, and executable `run.py`.
- Tool manifests include origin, review state, and safety state metadata.
- Search considers task, context words, tags, triggers, evidence, and confidence.
- Prompt recipes route through ordinary consent and quota controls.
- Script tools begin as drafts and unapproved.
- Script execution requires explicit approval and a global enable flag.
- Disabling preserves files and registry evidence.

## Dashboard

- Loopback dashboard loads without exposing keys.
- Provider, usage, route, quota, library, and pattern panels render.
- Pattern analysis can be triggered without executing scripts.
## Credential Wizard Tests

- Discover a provider key referenced by Codex `model_providers.*.env_key`.
- Preserve exact credential values containing `${...}`, quotes, and backslashes.
- Confirm pasted values remain visible and are printed exactly before acceptance.
- Verify the secret file is `0600` and its state directory is `0700`.
- Verify first-run non-interactive invocation exits without blocking MCP stdio or installation.
- Verify `init --force` never erases an existing credential file.


## TC-PREFLIGHT — Working lifecycle

- Preparation must make zero provider completion calls.
- Prompt, token budget, consensus plan, and route locks must be true before `working_may_begin`.
- Confirmation must be approved before plan execution.
- `run_prepared_task` must use the exact locked provider and model.
- A provider failure must return `repreflight_required` and must not invoke the router again.
- Consensus must lock voter and synthesis routes before any review call.
- CLI output must print preflight before the literal `Working...`.
