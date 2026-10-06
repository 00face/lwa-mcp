# Lwa MCP plugin

Codex plugin workflows use explicit skills. Invoke `$lwa` for orchestration,
`$lwa-plan` for preparation, `$lwa-sitrep` for evidence-backed reporting,
`$lwa-doctor` for diagnostics, `$lwa-verify` for verification, and
`$lwa-optimize` for prompt or conversation optimization. Native Codex `/model` and `/skills` remain
unchanged. This plugin does not register arbitrary `/lwa` or `/doctor`
commands.

This plugin installs the complete Lwa MCP server into Codex. The plugin points
at the maintained Lwa source tree and its Codex entrypoint, so every MCP tool
and the dashboard remain owned by the upstream project.

The server includes governed task preparation and execution, consent/quota
preflight, model routing, consensus, verification, SITREPs, planning, prompt
optimization, conversation compression, document editing, persistent tool
library search/read/run, workflow observation, and status/telemetry tools.

Text routing accepts `reasoning_effort=instant|medium|high` in addition to the
existing Lwa `quality` preference. The effort is locked during preflight and is
translated only by models that advertise support; `instant` maps to the
deterministic provider `none` setting. This is an API-route control, not a way
to change Codex's host-owned model or reuse a ChatGPT subscription session.

Provider discovery is fail-closed: a provider whose first live model discovery
attempt fails has its unverified seed models disabled and is labeled
experimental. Providers that are merely configured without live discovery are
reported as unverified, not as failed.

Routing intent is explicit and auditable through `set_routing_mode`,
`use_provider`, `clear_provider_stickiness`, and `refresh_provider_quotas`.
Only authoritative quota exhaustion can advance a locked named fallback chain;
transport, configuration, and capability failures stop for repreflight.

The launcher is intentionally absolute because the source project is outside
the Codex workspace:

`/home/face/Documents/Documents/code/lwa-mcp/scripts/codex-mcp-entrypoint.sh`

After installing or upgrading the plugin, start a fresh Codex conversation so
the host loads the plugin MCP process and its complete tool list.
