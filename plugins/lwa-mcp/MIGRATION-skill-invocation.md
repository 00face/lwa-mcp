# Skill invocation migration

Repository: `/home/face/.codex/plugins/lwa-mcp`
Baseline: 0.4.2

The documented entry point is `$lwa`, with focused explicit skills `$lwa-plan`,
`$lwa-sitrep`, `$lwa-doctor`, `$lwa-verify`, and `$lwa-optimize`. Existing MCP behavior remains the backing
system; the strict prepare/approve/run lifecycle, routing, quota, cost,
fallback, secret, and tool-library rules are retained in the skills.

Repository-owned legacy Codex command files and the installer path that copied
them to `~/.codex/commands` and `~/.codex/prompts` were deprecated/removed.
The dashboard remains a CLI operation. Native `/skills` and `/model` remain
unchanged.

Validation: manifest and skill metadata checks passed. The offline suite ran 59
tests with 58 passing and one environment-sensitive dashboard failure because a
dashboard was already reported running. Provider access and interactive Codex
skill discovery were not run.
