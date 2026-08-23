# SITREP 000 — Lwa MCP Baseline

**Date:** 2026-07-24  
**Status:** v0.4.0 implemented and offline-validated; live provider authentication remains an operator-controlled action.

## Completed

- Retained provider routing, quality escalation, consent gates, quotas, dashboard monitoring, and the persistent cross-project tool library; dynamic failover is now replaced by strict re-preflight after failure.
- Added a first-run credential wizard to the installer and `lwa-router init`.
- Added manual rerun commands through `lwa-router keys` and `scripts/configure-keys.sh`.
- Added recognized key discovery from Codex/process environment variables, Codex model-provider `env_key` references, Codex MCP environment maps, and fixed Codex/project `.env` files.
- Added intentionally visible terminal entry and exact-value confirmation.
- Added atomic protected `.env` writing, non-destructive reconfiguration, and exact literal loading.
- Preserved the rule that Codex OAuth session credentials are not repurposed as third-party provider API keys.

## Evidence

- Python source compilation: PASS.
- YAML/Pydantic configuration parse: PASS.
- Offline unit tests: 11 PASS.
- Visible credential entry and confirmation: PASS.
- Codex provider credential discovery: PASS.
- Exact `${...}`, quote, and backslash value round-trip: PASS.
- Secret file `0600`: PASS.
- State directory `0700`: PASS.
- Automatic three-observation tool creation: PASS.
- Per-tool README, manifest, launcher, and catalog generation: PASS.
- Script entry review gate: PASS.

## Known constraints

- Provider model catalogs, account entitlements, and free allocations remain volatile.
- Remote balance APIs are not standardized.
- Visible credential entry leaves values in terminal scrollback by operator request.
- The wizard intentionally avoids recursive home-directory, shell-history, browser-store, and keyring scraping.
- Script execution remains unavailable until both tool approval and global configuration allow it.

## Next operator actions

1. Install or upgrade Lwa MCP.
2. Complete the first-run visible credential wizard.
3. Run `lwa-router doctor`.
4. Register `[mcp_servers.lwa]` in Codex or the chosen MCP client.
5. Validate model-switch confirmation behavior.
6. Confirm tool-library discovery and dashboard visibility.

- Strict preflight now locks prompts, token budgets, consensus routes, and models before Working begins.
