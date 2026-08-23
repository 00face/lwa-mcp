# TR-082 — Terminal Host Capability Contract Rite

Status: complete

Execute before any terminal-specific adapter work.

1. Build the ten-terminal capability matrix and define the two allowed modes.
2. Add red-first tests for detection, overrides, missing binaries, and
   fail-closed diagnostics.
3. Implement normalized capability records with redacted debug output.
4. Verify that no code path silently falls through to an untouched Codex
   process in the current terminal.
5. Run the focused matrix tests and record results in the work order.

Result: every named terminal has an explicit split/window classification,
`LWA_TERMINAL_ADAPTER` is supported, and unavailable hosts fail with a
recoverable diagnostic. Evidence is recorded in
`reports/WO-082-086-terminal-compatibility-evidence.md`.
