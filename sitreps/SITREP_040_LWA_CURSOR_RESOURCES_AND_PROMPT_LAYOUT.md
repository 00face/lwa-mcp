# SITREP 040 — LWA cursor, resources, core engines, and prompt layout

## Current assessment

The Alt-arrow native transport is now deterministic, but LWA still has several
overlapping state owners: curses key decoding, the prompt editor, the focus
broker, tmux pane focus, feed scrolling, and the native render loop. This makes
cursor behavior sensitive to whether a terminal delivers a key as an integer
or a string and makes regressions difficult to localize.

The render loop also performs frequent full-frame work while streaming, pets,
graphics, and scrolling are all active. The project has privacy-safe debug
logging, but it needs explicit budgets and measurements rather than relying on
operator memory pressure observations.

Finally, LWA feed/status/prompt/suggestion rows share a constrained frame. A
response or modal can visually compete with the prompt even when the underlying
editor state is correct.

## Forge sequence

1. **WO-112 / TR-112:** establish cursor and focus invariants.
2. **WO-113 / TR-113:** add resource budgets and graceful degradation.
3. **WO-114 / TR-114:** lint and optimize core engines using measurements.
4. **WO-115 / TR-115:** refactor LWA prompt/feed geometry and separation.

This order prevents layout work from hiding input ownership or resource leaks.

## Validation standard

“Done” requires passing tests plus operator evidence for Ghostty/tmux, because
physical key normalization, mouse selection, and graphics behavior cannot be
fully established by unit tests alone. Logs must remain metadata-only: no prompt
bodies, credentials, environment values, or provider secrets.

