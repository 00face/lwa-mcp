# TR-056 — Native LWA Scroll Stability Rite

**Work order:** [WO-056](../workorders/WO-056-native-scroll-stability.md)
**Mode:** deterministic input reproduction and lifecycle hardening

**Current result:** Local scroll handling, mouse escape-sequence consumption,
unsupported-key isolation, and post-EOF stability are implemented. Focused
and full application gates pass. Raw arrow/Delete sequences are decoded and
Backspace/Delete remove prompt characters. A real-terminal key/scroll check
remains operator-verified.

## Sequence

1. Reproduce the failure with a fake curses screen that emits scroll-related
   key codes immediately after frame startup and after Codex EOF.
2. Trace every scroll event to confirm whether it reaches PTY write, resize,
   prompt mutation, or frame drawing code.
3. Introduce an explicit local scroll policy with bounded history and no PTY
   side effects.
4. Guard curses mouse decoding and unsupported integer key values.
5. Verify scroll behavior while the Codex process is active, exiting, and
   already closed.
6. Verify prompt routing remains unchanged for Tab, Enter, Backspace, Ctrl-C,
   printable input, and Esc.
7. Run focused native terminal tests followed by the full application suite.
8. Perform the real-terminal operator scroll gate and record the result.

## Evidence required

- Input trace showing scroll keys do not write to Codex.
- Lifecycle trace showing scroll-after-EOF does not raise.
- Test totals and any visual-only gate status.
- Confirmation that the terminal restores after exit.

## Promotion rule

Do not close this rite based solely on successful startup. Scroll must be
exercised after output is present and during or immediately after Codex exit.
