# WO-094 Pet Track Loading and Switching Evidence

Date: 2026-08-23
Status: Implementation complete; native visual switching gate open

## Implemented

- Added immutable `PetPlaybackState` in the pet renderer.
- Moved idle/welcome/action/completion track partitioning out of the terminal
  loop.
- Reduced the default idle track to the six-frame base idle sequence.
- Added one-time welcome playback on pet load.
- Added prompt-triggered action tracks with cooldown and return-to-idle.
- Added completion playback for successful LWA prompt synthesis.
- Pet candidates are fully loaded and normalized before active state changes.
- Invalid or failing pet loads retain the previous pet and report a redacted
  rejection instead of terminating the TUI.
- Added a generation to playback signatures so stale placements cannot be
  accepted after a switch.

## Verification

```text
Ruff                                                     PASS
Focused pet/native tests                                 40 passed
Full suite                                                263 passed, 3 skipped, 2 warnings
```

## Gate status

| Gate | Status | Evidence |
|---|---|---|
| Track separation | PASS | Playback-state unit test verifies distinct idle, welcome, action, and completion tracks. |
| Short idle loop | PASS (automated) | Idle is six frames and no longer includes later welcome/completion ranges. |
| Trigger cooldown | PASS (automated) | Repeated events during an active action are ignored until the track completes. |
| Failure containment | PASS (automated path) | Candidate loading exceptions are caught and active state is retained. |
| Full regression suite | PASS | 263 passed, 3 skipped. |
| Live pet switching | OPEN | Requires operator switch testing in Ghostty/tmux. |
| Live welcome/action/completion visuals | OPEN | Requires visual confirmation of the authoritative pet’s semantics. |

## Operator rite

Start a fresh `lwa` session in Ghostty and confirm:

1. Welcome plays once, then only the short idle loop repeats.
2. Submit a harmless prompt and observe one action track followed by idle.
3. Complete an LWA pipeline and observe completion followed by idle.
4. Switch between at least three configured pets five times.
5. Confirm no crash, duplicate, stale pet, blink, or prompt contamination.

The cache has no official trigger manifest, so the semantic mapping remains an
isolated loader policy and must be replaced if Codex later exposes explicit
track metadata.
