# WO-049 — Native Lwa Codex Terminal Frame

**Status:** Partial — a curses-based LWA frame and direct `lwa codex` bypass
exist; persistent interactive PTY framing, native graphical-terminal
integration, prompt compression, and cross-platform parity remain.
**Latest evidence (2026-08-21):** Persistent PTY framing, dual prompt surfaces,
resize/interrupt cleanup, shared prompt finalization, and focused lifecycle
checks pass. See [WO-049 evidence](../reports/WO-049-native-frame-evidence.md);
real desktop and native-renderer runs remain open.
**Priority:** P0
**Parent:** WO-015, WO-018, WO-048
**Task rite:** [TR-049](../task-rites/TR-049-native-lwa-codex-terminal-frame.md)

## Objective

Make bare `lwa` launch a reliable terminal-first LWA frame around Codex while
preserving `lwa codex` as an explicit direct-native bypass and keeping all LWA
dashboard functionality additive.

## Contract

- Bare `lwa` enters the LWA frame; `lwa codex` bypasses the frame and launches
  native Codex directly.
- The frame presents LWA Feed, Codex Feed, Codex Prompt, and LWA Prompt with
  keyboard-first navigation and a safe exit.
- The framed session uses a persistent interactive PTY rather than launching
  an unrelated one-shot completion for every prompt.
- Native graphical-terminal integration is capability-detected. When Ghostty
  or another supported renderer is available, LWA may attach/launch through it;
  otherwise the bounded terminal frame remains usable without pretending to be
  Ghostty.
- LWA-owned child processes are tracked, resized, cancelled, and reaped.
- Prompt finalization/compression happens before LWA Prompt input reaches the
  Codex PTY, with an explicit raw/direct mode.
- Terminal output is not copied into persistent logs by default. Secrets,
  prompts, and authorization material stay out of telemetry.

## Required Work

1. Replace the current one-shot curses execution path with an interactive PTY
   session and event loop that preserves Codex TUI behavior.
2. Add terminal geometry negotiation, signal handling, suspend/continue,
   cancellation, process-group cleanup, and terminal restoration on exit.
3. Define native renderer adapters for Ghostty-capable Linux hosts and a
   dependency-light fallback for systems without that renderer.
4. Share session events and prompt-finalization logic with WO-048 rather than
   creating a second compression or routing implementation.
5. Add tests for resize, Ctrl-C, EOF, crash, terminal restoration, direct
   bypass, and no-orphan-process behavior.
6. Verify the frame under low memory, narrow terminals, missing Codex, missing
   renderer, Unicode input, and long-output conditions.

## Acceptance

- `lwa` opens the frame and retains terminal control until the user exits;
  `lwa codex` remains a working direct bypass.
- Codex can run an interactive session with input, output, resize, interrupts,
  and clean exit without leaving the shell in raw mode.
- LWA Prompt and direct Codex Prompt are distinct, labeled, and auditable.
- The same preservation/compression contract and redaction rules as WO-048 are
  exercised from the terminal surface.
- Native renderer availability and fallback behavior are reported honestly.
- Focused tests pass on Linux Mint-class hardware without requiring a paid
  provider route or storing raw prompt fixtures.

## Evidence

Store redacted results under a future `reports/WO-049-*` artifact. Include
terminal mode, renderer selection, session lifecycle, resize/interrupt results,
resource measurements, and prompt-preservation assertions.

## Rollback

Restore bare `lwa` to the last known-safe direct launcher or disable only the
framed session feature. Leave `lwa codex`, the web Observatory, MCP server, and
user state intact. Restore terminal settings before returning control to the
shell.
