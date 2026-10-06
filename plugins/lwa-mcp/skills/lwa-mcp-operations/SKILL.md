---
name: lwa-mcp-operations
description: Use Lwa MCP for governed routing, preflight, planning, verification, SITREPs, optimization, and reusable tools.
---

# Lwa MCP operations

This implementation-facing skill is reached through the explicit `$lwa`
workflow. Text after `$lwa` is the user's task, constraints, and requested
Lwa operation. It is not a native `/lwa` command.

Use the Lwa MCP tools when a task benefits from model routing, cost/consent
controls, reusable workflow tools, or durable engineering reporting.

For provider work, prepare first, approve the returned preflight when required,
then run the single-use prepared task. Paid and user-pays routes are disabled by
default; enable each only with explicit operator intent and a configuration
allowance. Do not claim Working has begun before the preflight says it may
begin. For recurring workflows, search the persistent tool library and record
successful outcomes with `observe_workflow`.

For engineering progress, use `write_sitrep` and `plan_work`/`work_order`-
style planning tools to leave evidence, next actions, and acceptance criteria.
