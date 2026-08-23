# SITREP 014 — Codex skill invocation migration

## Scope

Migrate Codex-facing Lwa workflows from repository-owned slash-command
shortcuts to explicit `$skill-name` invocation while preserving the MCP server,
strict preflight lifecycle, routing, cost/quota controls, provider fallback,
credential handling, and reusable tool library.

## Result

- `$lwa`, `$lwa-plan`, `$lwa-sitrep`, and `$lwa-doctor` are packaged by the Codex plugin.
- All four skills require explicit invocation.
- The repository no longer installs user-global Codex command or prompt files.
- Native `/skills` and `/model` are documented as native Codex controls.
- The dashboard URL remains available through `lwa-router doctor --show-dashboard-url`.

## Validation

The plugin manifest and skill metadata checks passed. The offline suite ran 59
tests: 58 passed and one failed because an already-running dashboard made an
environment-sensitive assertion report `dashboard_running=true` where the test
expected false. Interactive Codex skill discovery and live provider access
remain unverified.

## Rollback

Restore the removed `.codex/commands/*.md` files and the prior installer only
from a reviewed pre-migration copy. Do not write to user-global Codex paths as
part of rollback without explicit authorization.
