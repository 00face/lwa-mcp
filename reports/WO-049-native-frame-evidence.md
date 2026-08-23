# WO-049 / TR-049 Evidence

**Recorded:** 2026-08-21  
**Result:** Partial promotion; persistent frame and focused lifecycle checks
pass, full desktop rite remains open.

## Redacted checks

- Bare `lwa` still selects the LWA frame; `lwa codex` remains the explicit
  direct-native bypass; `lwa-web` remains additive at `/codex`.
- The frame now owns one persistent `CodexSession` PTY for its lifetime. It no
  longer launches a separate `codex exec` child per prompt.
- Codex Prompt sends direct PTY input. LWA Prompt passes through the shared
  finalization boundary and visibly reports the explicit semantic bypass when
  no governed compressor is configured.
- Tab switches between labeled prompt surfaces; Ctrl-C is sent to the Codex
  PTY; terminal geometry is negotiated on resize; `curses.wrapper` restores
  terminal state on normal and exceptional exits; the session closes in a
  `finally` block.
- The renderer label reports Ghostty host availability honestly as
  `ghostty-host / Lwa fallback frame`; unsupported hosts report
  `curses fallback frame`.
- Focused verification: `12 passed` across web frame, native frame, broker,
  launcher, prompt boundary, and renderer capability tests.

## Outstanding rite checks

- Interactive verification in a real Linux Mint terminal for shell echo,
  alternate-screen state, Ctrl-C, EOF, crash recovery, and orphan-process
  inspection.
- Native Ghostty adapter beyond host-capability labeling, plus low-memory and
  narrow-terminal runs with long Unicode output.
- Resource measurements and a real Codex interactive smoke run.
