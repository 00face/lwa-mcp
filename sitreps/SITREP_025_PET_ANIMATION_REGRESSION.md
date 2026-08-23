# SITREP 025 — Pet Animation Regression

Date: 2026-08-22
Status: Open

## Situation

The Codex `dewey` pet cache is healthy: LWA resolves the configured identity,
loads authoritative PNG frames, and sees multiple distinct animation frames.
The native Ghostty/tmux presentation remains static during live use.

## Assessment

The regression is in the native presentation layer, not the asset layer.
Recent changes moved between repeated Kitty transmission, terminal-owned
animation, and preloaded placement in response to visible leakage and
flashing. The last reported animated state is not currently backed by a
reproducible source checkpoint, so an automatic rollback would risk restoring
the prompt corruption observed earlier.

## Decision

Do not regress blindly. WO-092/TR-092 define a controlled comparison of the
three protocol strategies. A rollback is permitted only if the prior animated
behavior can be reproduced and passes input isolation and fixed-placement
gates.

## Gates

- Asset integrity: **green**.
- Protocol generation: **green**.
- Ghostty/tmux visual animation: **red** — pet is static.
- Prompt/input isolation: **previously red/unstable** during repeated frame
  transmission; must be revalidated.
- Fallback rendering: **green**.

## Next action

Execute TR-092 in sequence and record the first protocol that passes all
visual and input gates. No additional animation protocol should be invented
outside that comparison.
