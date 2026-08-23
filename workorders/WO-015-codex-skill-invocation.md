# WO-015 — Codex skill invocation migration

Status: Partial
Priority: P0
Owner: Lwa MCP maintainers
Date: 2026-08-02

## Objective

Expose Lwa's Codex-facing workflows through explicit skills while retaining the
MCP server as the deterministic backing system and preserving strict preflight,
provider routing, quota/cost controls, fallback, secret containment, and the
reusable tool library.

## Work packages

1. Package `$lwa`, `$lwa-plan`, `$lwa-sitrep`, `$lwa-doctor`, `$lwa-verify`, and
   `$lwa-optimize` with explicit-only metadata.
2. Remove repository-owned Codex command shortcuts and prevent installation to
   user-global `~/.codex/commands` and `~/.codex/prompts`.
3. Update onboarding, architecture, operator, README, and migration records.
4. Validate manifest, skill metadata, MCP handshake, offline behavior, and
   fresh-session Codex discovery.

## Acceptance

- [x] Plugin manifest and skill metadata validate.
- [x] MCP handshake passes: protocol `2025-11-25`, 35 tools, 3 resources, 1 prompt.
- [x] Native `/skills` and `/model` remain documented as native Codex controls.
- [x] Offline dashboard lifecycle test is isolated from an existing dashboard
      process; full suite and packaging verification pass.
- [ ] Fresh Codex session discovers and invokes `$lwa` and a focused skill.
- [ ] Live provider checks remain separately authorized and opt-in.

## Evidence and rollback

See `SITREP_014_SKILL_INVOCATION_MIGRATION.md` and the central TR-003 record.
Rollback restores reviewed repository files only; it does not write user-global
Codex command files or restore provider credentials.
