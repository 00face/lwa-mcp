---
name: lwa
description: Orchestrate Lwa MCP preflight, model routing, quota and cost controls, consensus, optimization, reusable tools, and evidence-backed project operations.
---

# Lwa MCP

Use `$lwa` as the explicit Codex plugin entry point. Text following `$lwa` is
the user's objective, constraints, quality mode, reasoning effort, and requested
operation. Do not describe this as a native `/lwa` command.

## Required lifecycle

1. Search the reusable library with `suggest_library_tools` and inspect a
   matching candidate with `read_library_tool` before rebuilding recurring work.
2. Call `prepare_task` or the relevant specialized preparation tool.
3. Inspect route, model, token budget, quota, cost class, consent, consensus,
   reasoning effort, and fallback locks. Call `approve_preflight` when required.
4. Only after `working_may_begin=true`, announce execution and call
   `run_prepared_task` once. A non-quota route failure requires repreflight;
   never reroute silently during execution. An authoritative quota-exhaustion
   result may advance only through the locked, named fallback chain while
   preserving the prompt, token budget, consent, and capability constraints.
5. Record validated recurring workflows with `observe_workflow`; review any
   script source before approval or execution.

Preflight uses the configured seed/live catalog already in memory. It does not
silently refresh provider catalogs. Use `refresh_model_catalog` or
`pipeline_status(probe=true)` only when live control-plane evidence is needed.
An offline provider status of `ready` means configured for a seed route; inspect
`readiness` and `live_verified` before describing a service as reachable.

Use `set_routing_mode`, `use_provider`, `clear_provider_stickiness`, and
`refresh_provider_quotas` to make routing intent explicit and auditable.

## Restrictions

Keep provider keys out of prompts, reports, logs, and generated documentation.
Respect local cost and quota caps, explicit consent, and fallback boundaries.
MCP tools remain the deterministic backing system; this skill coordinates them
and does not replace them with prose.

Use `reasoning_effort=instant|medium|high` when the provider route must carry an
explicit reasoning setting. This is distinct from Lwa's `quality` routing
preference. `instant` is deterministic and does not request provider-side
automatic escalation.
