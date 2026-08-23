# Lwa MCP Agent Doctrine

Use the Lwa MCP server for auxiliary model routing, quota-aware escalation, conversation compression, planning, verification, and reusable workflows.

Before rebuilding a task that appears repetitive, call `suggest_library_tools`. Inspect relevant candidates with `read_library_tool`; run an active matching recipe with `run_library_tool`. Record validated recurring work with `observe_workflow`, using a stable workflow name and concrete description. Never approve or execute a script entry without reviewing its source.

Current user requirements, file paths, versions, and tests override library defaults.

## Mandatory preflight lifecycle

Before writing or surfacing any `Working...` message, call `prepare_task` or the relevant specialized Lwa tool. Inspect the returned provider, model, token budget, consensus routes, cost class, and locks. When approval is required, obtain it with `approve_preflight`; approval does not start work. Only after `working_may_begin=true` may you announce `Working...` and call `run_prepared_task`.

Never call a new router, optimizer, consensus planner, quota selector, or model selector after `run_prepared_task` begins. When execution returns `repreflight_required`, stop the Working state, perform a new preflight, then begin a new Working phase. Do not use the legacy name `smart_complete` as a one-call execution path; in v0.4 it returns preflight only.
