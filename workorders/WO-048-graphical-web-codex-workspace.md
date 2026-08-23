# WO-048 — Graphical Web Codex Workspace

**Status:** Partial — `/codex`, the PTY bridge, bounded canvas terminal, LWA/Codex prompt surfaces, and optional WebGL shader pass exist; persistent-session hardening, semantic compression, graphics compatibility, and resource benchmarks remain.
**Latest evidence (2026-08-21):** Session broker, disconnect cleanup, prompt-finalization redaction, and focused route/lifecycle checks pass. See [WO-048 evidence](../reports/WO-048-web-codex-evidence.md); browser graphics and resource rite checks remain open.
**Priority:** P0
**Parent:** WO-016, WO-018, WO-046
**Task rite:** [TR-048](../task-rites/TR-048-graphical-web-codex-workspace.md)

## Objective

Make `lwa-web` an additive graphical Codex workspace while preserving the
existing Observatory dashboard at `/`. The workspace must provide a local,
low-resource, PTY-backed terminal surface with LWA framing and a safe path for
future prompt compression before Codex receives input.

## Contract

- `/` remains the Observatory and existing dashboard/API behavior remains
  available.
- `/codex` is the framed workspace with Codex Feed, Codex Prompt, LWA Feed,
  and LWA Prompt surfaces.
- `lwa-web` opens `/codex`; it never replaces or redirects the Observatory.
- Codex sessions remain local and loopback-bound. A browser client cannot cause
  arbitrary host-process execution outside the session broker contract.
- The PTY/session bridge supports connect, input, prompt handoff, resize,
  disconnect, cancellation, and bounded cleanup.
- Terminal history is bounded; raw prompt bodies and credentials do not enter
  telemetry, browser storage, or diagnostic artifacts by default.
- Canvas/WebGL rendering is progressive enhancement. Low Resource mode must
  remain usable without WebGL, animation, or shader effects.
- Shader effects are capped and pausable; terminal redraws are event-driven or
  rate-limited rather than continuously busy-looping.
- LWA Prompt passes through a dedicated prompt-finalization/compression hook
  before Codex input. If compression is unavailable, the bypass is explicit
  and visible rather than silently claimed as compression.

## Required Work

1. Replace the current one-connection PTY lifecycle with a bounded session
   broker that can safely attach the web client, terminal client, and dashboard
   telemetry to one session.
2. Add session identity, disconnect cleanup, resize validation, process
   cancellation, and loopback authorization/handshake checks.
3. Implement the semantic-compression hook for LWA Prompt, preserving literal
   paths, identifiers, commands, acceptance criteria, and unresolved work.
4. Expand terminal parsing and graphics compatibility tests for ANSI/VT,
   Unicode, hyperlinks, clipboard/input behavior, Kitty or Sixel capability
   detection, and image fallback behavior.
5. Benchmark startup, idle memory, redraw rate, scrollback, shader-on, and
   Low Resource mode on a 7 GiB Linux host.
6. Add keyboard/focus, screen-reader status, pause/scroll-lock, and visible
   error-state verification.

## Acceptance

- Observatory routes and existing dashboard tests remain green.
- A browser can open `/codex`, start one Codex session, submit LWA and direct
  prompts, resize the terminal, and stop the session without orphaning a
  process.
- The same session exposes bounded, redacted telemetry to the Observatory.
- Low Resource mode works without WebGL and stays within the agreed memory and
  redraw budgets.
- Shader and graphics capability checks are explicit; unsupported features
  degrade to text or a static image placeholder.
- Compression tests prove that protected literals and constraints survive the
  handoff, and bypass mode is visibly labeled.
- No credential, authorization header, raw prompt, or session token appears in
  logs or saved evidence.

## Evidence

Store redacted results under a future `reports/WO-048-*` artifact. Include
browser route status, session lifecycle events, renderer mode, capability
matrix, resource measurements, and structural prompt-preservation assertions.

## Rollback

Disable `/codex` session creation and leave `/` Observatory and existing MCP
routes active. Stop only LWA-owned child processes, preserve redacted
telemetry, and fall back to direct `codex` or the existing dashboard without
deleting user state.
