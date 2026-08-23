# WO-056 — Native LWA Scroll Stability

**Status:** Implemented — automated gates pass; operator-visible key/scroll gate remains
**Parent:** WO-054, WO-055
**Task rite:** [TR-056](../task-rites/TR-056-native-scroll-stability.md)

## Objective

Make native `lwa` stable when the user scrolls, including mouse-wheel input,
keyboard navigation, Codex redraws, and scroll events occurring as Codex exits.

## Failure contract

- Scrolling must never be forwarded as accidental prompt text.
- Mouse events and unsupported curses key codes must be safely ignored or
  handled as local frame navigation.
- A scroll event must not trigger PTY resize or write operations.
- Codex output and the LWA frame must remain readable after scrolling.
- Codex completion during scrolling must not crash or close the LWA frame.
- The screen must restore normally after Esc or an orderly exit.

## Acceptance gates

1. Fake curses tests cover `KEY_MOUSE`, wheel buttons, `KEY_UP`, `KEY_DOWN`,
   PageUp, PageDown, and unsupported integer key codes.
2. Scroll input produces no `CodexSession.write()` calls.
3. Scroll input produces no unexpected resize calls.
4. Scroll during Codex EOF leaves the frame alive until Esc.
5. Narrow and normal terminal sizes remain safe while scrolling.
6. Focused and full application tests pass.
7. An operator-visible scroll check confirms no crash in a real terminal.

## Rollback

Disable local scroll handling and ignore all non-text curses key codes while
retaining prompt, interrupt, and exit controls.
