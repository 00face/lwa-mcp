---
name: lwa-plan
description: Prepare a Lwa MCP technical plan with locked routing, token, quota, consent, and acceptance constraints before execution.
---

Use `$lwa-plan` followed by the planning objective and constraints. Call
`plan_work` or `prepare_task`, inspect the returned locks, and report the plan
without beginning provider execution. Keep the strict preflight lifecycle and
do not announce Working until approved.
