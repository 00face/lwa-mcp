# History

## 0.4.1 — 2026-07-25

- Added WO-014 and Rite 8 to track cross-project provider credential scope,
  OpenAI/ChatGPT and Gemini readiness, and strict pro-route intent.
- Recorded the MSF evidence boundary: project-local `GEMINI_API_KEY` guidance
  exists, but no dedicated Codex/Lwa logs or live entitlement proof was found.

## Unreleased — 2026-08-02

- Opened WO-016 and Rite 9 for canonical task/quality syntax, specialized
  pipeline selection, and public prompt-template variable validation.
- Recorded that invalid `task` and `quality` values were rejected before
  routing; a corrected locked ZAI call proved connectivity but not universal
  pipeline correctness.
- Completed WO-016/Rite 9 with canonical boundary validation, public/internal
  prompt-variable separation, and 87-test regression evidence.
- Opened WO-017/Rite 10 for documented Puter/SiliconFlow health handling and
  WO-018/Rite 11 for separate native TUI/global-MCP startup evidence.
- Safe execution refreshed provider health (Puter 404, SiliconFlow 401) and
  reran the reversible fast-start CLI probe (`FAST_OK`, 8.90s); no paid or
  user-pays call was made and native TUI acceptance remains open.
- Applied the quirk-baseline health gate: explicitly unhealthy providers no
  longer route through stale seed models; full regression reached 88 passed.
- Opened WO-019/Rite 12 for bounded Puter schema evidence and a provider-specific
  discovery adapter, WO-020/Rite 13 for an authorized redacted SiliconFlow
  model check, WO-021/Rite 14 to preserve the health gate, and WO-022/Rite 15
  for native TUI/global-MCP startup evidence.
- Completed the Puter bounded schema check and provider-specific adapter (538
  live models); completed the redacted SiliconFlow check (401 remains); and
  verified the health gate with 89 full-suite passes. Native TUI reached the
  prompt but MCP initialization remained interrupted, so WO-022 is partial.
- A second ephemeral TUI comparison reached the prompt after sequential MCP
  startup progress without a warning banner; first-response timing and durable
  attribution remain open.
- Opened WO-023/Rite 16 for server-by-server MCP attribution and first-response
  timing. Prompt readiness is evidenced; the external response probe remains
  gated to avoid an unapproved model invocation.
- Added `/home/face/.codex/quirks/quirk_tui_plugin_design.md`, defining feasible
  companion-renderer/editor patterns and the boundary against undocumented host
  TUI screen injection.

# History

## 0.4.1 — 2026-07-24

- Added consent-mode parsing compatibility for `always_ask`/`automatic` alongside legacy aliases.
- Extended reusable tool manifests with explicit origin, review state, and safety state metadata.
- Added prioritized release work orders, v0.4.1 SITREP, and source/wheel/archive/checksum artifacts.
- Added centralized provider-error redaction, bounded reviewed-script output, and dashboard version alignment.
- Added explicit unsupported-streaming behavior, request-size limits, and offline provider contract coverage.
- Tightened CLI, dashboard, and server consent-mode handling so config, API, and docs share the same names.

## 0.4.0 — 2026-07-24

- Added mandatory two-phase preflight and execution.
- Locked prompt, token budget, consensus topology, and model routes before Working.
- Added single-use plan and approval tokens.
- Disabled dynamic rerouting during active work; failures require a new preflight.
- Added dashboard preflight ledger and strict CLI Working ordering.
- Changed convenience MCP tools and legacy smart-complete aliases to preparation-only behavior.


## 0.3.0 — 2026-07-24

- Added a first-run interactive credential wizard invoked by `lwa-router init` and the installer.
- Added independent `lwa-router keys` and `scripts/configure-keys.sh` entry points.
- Added recognized credential discovery from the current Codex/process environment, Codex model-provider `env_key` references, Codex MCP environment maps, and fixed Codex/project `.env` locations.
- Kept credential entry intentionally visible and added exact-value confirmation before saving.
- Added atomic secret-file replacement, `0600` file permissions, and `0700` state/config directory permissions.
- Disabled dotenv interpolation so credentials containing `${...}` remain exact.
- Made `init --force` non-destructive to existing secrets.
- Added tests for Codex discovery, visible confirmation, exact credential round-tripping, and filesystem permissions.
- Expanded offline tests from eight to eleven.

## 0.2.0 — 2026-07-24

- Renamed the project and command surface to Lwa MCP.
- Moved configuration, state, and data into dedicated `lwa-mcp` XDG namespaces.
- Added persistent cross-project tool library with registry, generated catalog, per-tool manifests, READMEs, and Python launchers.
- Added deterministic repeated-workflow detection with local evidence, confidence, success counts, and privacy-preserving prompt hashes.
- Added automatic prompt-recipe creation after the configured successful-observation threshold.
- Added MCP and CLI interfaces for search, suggestion, inspection, execution, creation, observation, analysis, approval, and disabling.
- Added dashboard panels for reusable tools and workflow patterns.
- Added review-gated script registration and disabled-by-default script execution.
- Added non-destructive migration from the previous Castor & Pollux baseline.
- Expanded tests from six to eight, including automatic tool generation and script review gating.

## 0.1.0 — 2026-07-24

- Established the original standalone auxiliary model router.
- Added requested provider configurations, live catalog merging, task scoring, quality-sensitive escalation, consent modes, local caps, bounded failover, usage ledger, dashboard, and auxiliary task tools.
