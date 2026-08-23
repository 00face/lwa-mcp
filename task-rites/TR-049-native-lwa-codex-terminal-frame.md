# TR-049 — Native Lwa Codex Terminal Frame Rite

**Purpose:** prove that the terminal-first LWA frame preserves interactive
Codex behavior, shell safety, and a clean escape path on constrained Linux
systems.

**Current result (2026-08-21):** Partial promotion. The persistent session
event loop and deterministic unit checks pass; real terminal restoration,
renderer, resource, and orphan-process checks remain.

## Entry

Record terminal dimensions, shell, OS, Codex executable, renderer availability,
and Low Resource setting. Confirm the working tree and user state are not used
as disposable test targets.

## Action

1. Launch bare `lwa`; confirm the LWA frame appears with labeled LWA and Codex
   regions.
2. Start an interactive Codex session, type through both prompt paths, resize
   the terminal, interrupt a running operation, and exit normally.
3. Repeat with missing Codex, narrow dimensions, long output, Unicode, and no
   native graphical renderer.
4. Launch `lwa codex` and confirm it bypasses the frame without changing the
   Observatory or MCP registration.
5. Capture terminal restoration, child-process, renderer, resource, and
   redacted prompt-preservation evidence.

## Check

- Shell echo, cursor mode, alternate-screen state, signal handling, and
  terminal dimensions are restored after every exit path.
- No orphaned Codex/LWA child remains after exit, crash, or Ctrl-C.
- Direct bypass is distinguishable from framed mode in command output and
  telemetry.
- Low-resource behavior remains responsive and does not require shader/GPU
  support.
- Prompt finalization protects literal paths, commands, identifiers,
  acceptance criteria, and unresolved work; raw mode is explicitly labeled.

## Promote when

Repeated interactive runs pass on the target Linux Mint machine and one clean
fallback environment, with terminal restoration and process cleanup verified.

## Rollback

Stop using framed `lwa`, use `lwa codex`, preserve the evidence, and restore any
terminal settings before ending the rite. Do not reset the repository or delete
LWA state.
