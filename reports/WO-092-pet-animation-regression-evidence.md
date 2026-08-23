# WO-092 Pet Animation Regression Evidence

Date: 2026-08-22
Host: Linux Mint / Ghostty 1.3.1 / tmux 3.4

## Checkpoint

Current compositor checkpoint:

```text
image_compositor.py  6c212f418ecc758a61c3f07b85fe84d08f03f7dada51017622b285b2ed7307dc
terminal_frame.py    3481cc5b5314849dd807b74028c278e0b9a423dfe2c482746c517c027ef18f38
launch.py            321533f7afffc6d0ebe91ace3e356b27162e3cf5e8aa237902b597a4ed46eb6a
pet_renderer.py      f06096c1c6734701c53aba83dcbe7b5e694a41cb27cb1abe43f5d6698f231581
```

## Baseline gates

| Gate | Result | Evidence |
|---|---|---|
| Configured identity | PASS | Codex config selects `dewey`. |
| Asset integrity | PASS | 12 bounded frames loaded; 11 distinct payloads. Representative frame hashes differ. |
| Protocol shape | PASS | Terminal-owned, preloaded-placement, and client-replacement sequences are syntactically formed and terminated. |
| tmux geometry | PASS | Isolated tmux 3.4 probe reports `0,0,80,24`; passthrough is `on`. |
| Automated input safety | PASS | 61 relevant tests pass, including graphics-response filtering and prompt handling. |
| Live animation | FAIL | Operator reports the native pet remains static. |
| Historical rollback | NOT AUTHORIZED | The prior animated state also leaked protocol/cursor behavior and has no preserved source checkpoint. |

## Protocol comparison

The current implementation uses preloaded frame transmission (`a=t`) followed
by frame placement (`a=p`). The protocol is valid at the byte-shape level, but
the live host does not visibly switch frames. Terminal-owned animation and
client replacement are not accepted merely because their sequences are valid;
they require the same live visual and input gates.

## Decision

Do not regress to the earlier animated implementation yet. It is not a safe
rollback target because its observed behavior included blinking, cursor
coupling, and protocol leakage. The next change requires an isolated live
Ghostty probe that distinguishes whether Ghostty drops `a=p`, tmux drops the
passthrough sequence, or the frame IDs are not retained.

## New operator evidence

The independent-window matrix produced one visible animation result:
`C-client-same-id`. It still blinks at the animation loop boundary, but it
proves that same-ID client-driven replacement is accepted by Ghostty. This is
now the controlled native candidate; the static preloaded-placement path is
not the selected baseline.

## Remaining acceptance

- Three visible frame changes in five seconds.
- Fixed bottom-right placement after typing and resize.
- No graphics text or altered prompt input.

Until those checks pass, native animation remains open and the stable frame or
text fallback is the approved behavior.
