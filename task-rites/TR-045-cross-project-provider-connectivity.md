# TR-045 — Cross-project provider connectivity rite

**Purpose:** classify the runtime boundary and verify LWA control-plane and
provider metadata access without submitting completion prompts.

## Inputs

- `LWA_ROOT`: absolute LWA MCP repository root.
- `PROJECT_ROOT`: project root being tested.
- `LWA_MCP_CONFIG` and `LWA_MCP_ENV_FILE`: governed paths; record metadata only.
- A host capable of egress, or an explicitly declared restricted/offline
  environment.

## Procedure

1. **Record scope.** Print `PROJECT_ROOT`, `LWA_ROOT`, launcher path, config path,
   env path, file modes, and `execution_boundary`. Never print file contents.
2. **Check runtime.** Confirm the LWA virtualenv, `lwa-mcp`, and
   `check-mcp-handshake.py` exist and are executable.
3. **Classify network.** Resolve the provider hosts declared by the current
   config and make bounded HTTPS metadata requests. If DNS/egress is blocked,
   record `restricted` or `offline`; do not classify a provider as unhealthy.
4. **Run zero-payload discovery.** From `LWA_ROOT`, run:

   ```sh
   LWA_LIVE_PROVIDER_CHECK=1 PYTHONPATH=src \
     .venv/bin/python scripts/check-live-providers.py
   ```

   Require `completion_requests_made=0`. Preserve provider, configured,
   enabled, experimental, healthy, billing class, and bounded model-count
   fields only.
5. **Run MCP handshake.** Run:

   ```sh
   PYTHONPATH=src .venv/bin/python scripts/check-mcp-handshake.py --timeout 20
   ```

   Record protocol version, tool count, resource count, prompt count, and
   failure text after redaction.
6. **Check dashboard separately.** If the dashboard is requested, test its
   socket and log startup/exit independently. A dashboard failure does not
   invalidate the MCP result.
7. **Repeat from each project root.** Use the same `LWA_ROOT` and absolute
   launcher. Confirm project identity changes while provider configuration does
   not silently drift.

## Acceptance

- LWA root plus two project roots produce bounded, comparable evidence.
- Host runs report live provider health; restricted runs report the boundary.
- MCP and dashboard results are separate.
- No secret, prompt body, authorization header, or raw env value appears in
  stdout, stderr, or the saved artifact.
- A provider metadata PASS is never promoted to prompt-execution PASS.

## Stop and recover

- Missing runtime: fix the absolute launcher path and rerun.
- Restricted DNS/egress: rerun on the approved host boundary; do not rotate
  credentials or disable providers based only on this result.
- Handshake timeout: inspect the bounded server stderr and startup path; do not
  infer provider failure.
- Provider 401/403/429: preserve the typed provider result and start a fresh
  approved provider-specific investigation.
- Redaction violation: stop immediately, quarantine the artifact, and rotate
  exposed credentials before any live proof.

## Evidence artifact

`cross-project-connectivity.json` with a redacted summary, one row per project,
one row per provider, execution boundary, timestamps, and recovery actions.

