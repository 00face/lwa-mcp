# Version Control

## Unreleased

- Reforged the Codex Lwa plugin path: normal preflight no longer performs
  implicit live catalog discovery; provider discovery is explicitly bounded;
  pipeline status now exposes configured versus live-verified readiness; model
  tier output includes capabilities and catalog source; completion telemetry
  records transport and result provenance; and the entrypoint falls back to a
  PATH-installed `lwa-mcp` executable when the project virtualenv command is
  unavailable.
- Added WO-016 and SITREP 014 to govern canonical `TaskKind`, quality,
  pipeline-entry, and prompt-variable contracts.
- The planned contract keeps `{input}` public and
  `{{CONSENSUS_TRANSCRIPT}}` internal to locked consensus synthesis.
- Added WO-017/SITREP 015 and WO-018/SITREP 016 with explicit paid-execution
  switches and reversible TUI investigation boundaries.
- Gated stale seed models when live provider health is explicitly unhealthy;
  provider-specific 404/401 remediation remains pending evidence.
- Added WO-019 through WO-022 and SITREPs 017 through 020 for bounded Puter
  discovery, authorized SiliconFlow diagnostics, health-gate regression, and
  separate native TUI/global-MCP startup evidence.
- Implemented `PuterAdapter` after a bounded documented-schema check returned
  538 models; recorded SiliconFlow's redacted 401; and verified 89 full-suite
  tests. Native TUI startup evidence remains partial under WO-005/TR-007.
- Added WO-023/SITREP 021 and Rite 16 for durable MCP attribution and explicit
  first-response timing authorization.
- Added the TUI/plugin feasibility baseline at
  `/home/face/.codex/quirks/quirk_tui_plugin_design.md`.

## v0.4.1

- Added WO-014 provider-access and pro-route readiness contract.
- Added Rite 8 evidence record for MSF project-local Gemini configuration and
  cross-project Codex credential mapping gaps.

**Lifecycle:** strict preflight before execution.

- Added `preflight.py`, `PreflightSummary`, and locked route roles.
- Added `prepare_task`, `approve_preflight`, and `run_prepared_task`.
- Consensus voter and synthesis routes are preselected.
- Provider errors now return `repreflight_required` without mid-work model switching.
- Added SQLite `preflight_events`, dashboard rendering, and four preflight tests.


## v0.3.0

Public credential commands:

- `lwa-router init [--no-key-wizard]`
- `lwa-router keys`
- `scripts/configure-keys.sh`

Credential contract:

- Secret file: `~/.local/state/lwa-mcp/lwa.env`
- Secret file mode: `0600`
- State/config directory mode: `0700`
- Atomic same-directory replacement after `fsync`
- Exact-value loading without dotenv interpolation
- Recognized Codex/process and fixed `.env` discovery only
- Ordinary echoed terminal input plus exact-value confirmation
- Codex OAuth session data is not imported as a provider API key

Compatibility target remains Python 3.11+ and MCP Python SDK 1.x.

## v0.2.0

Public commands:

- CLI: `lwa-router init|doctor|run|library`
- MCP server: `lwa-mcp`
- Dashboard: `lwa-dashboard`

New persistent interfaces:

- `list_library_tools`
- `search_tool_library`
- `suggest_library_tools`
- `read_library_tool`
- `run_library_tool`
- `create_library_tool`
- `register_script_tool`
- `approve_library_tool`
- `disable_library_tool`
- `observe_workflow`
- `analyze_repeated_workflows`
- `rebuild_tool_catalog`
- `library_status`

Database additions:

- `workflow_patterns`
- `workflow_observations`

Persistent library contract:

- `registry.json`
- `CATALOG.md`
- `tools/<slug>/tool.yaml`
- `tools/<slug>/README.md`
- `tools/<slug>/run.py`

Compatibility target: Python 3.11+, MCP Python SDK 1.x. Previous baseline state can be copied with `scripts/migrate-from-castor-pollux.sh`.

## v0.1.0

Original auxiliary router baseline.
