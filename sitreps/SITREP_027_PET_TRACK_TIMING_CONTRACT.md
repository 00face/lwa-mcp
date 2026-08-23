# SITREP 027 — Pet Track Timing Contract

Date: 2026-08-23
Status: Analysis complete; change approved for implementation

## Situation

The current native pet timing was recently changed in the wrong direction:
idle was set to 80 ms per frame while welcome, action, and completion tracks
remain at 360 ms. This makes the idle loop unnaturally fast and makes active
animations feel sluggish.

## Proposed contract

| Track | Interval | Intended behavior |
|---|---:|---|
| Idle | 360 ms | Calm, clearly readable background motion. |
| Welcome | 120 ms | Brief responsive entrance animation. |
| Action | 120 ms | Responsive feedback to a prompt or event. |
| Completion | 120 ms | Responsive task-finished feedback. |

## Assessment

This contract is internally consistent. Idle is a low-frequency ambient loop,
while event-driven tracks are short and expressive. The scheduler must choose
the interval from the active track, not from whether the pet is generally
animated.

Action cooldowns must use the same 120 ms active-track interval so the action
cannot be retriggered while its frames are still playing. Idle must not inherit
the action cooldown or its faster cadence when it resumes.

## Required change

Set:

```text
NATIVE_PET_IDLE_INTERVAL = 0.36
NATIVE_PET_ACTION_INTERVAL = 0.12
```

No frame partitioning, image protocol, pet switching, or focus behavior should
change as part of this timing-only adjustment.

## Verification gates

- Unit/static gate: constants and scheduler selection match this contract.
- Action gate: welcome/action/completion cooldowns use 120 ms.
- Idle gate: idle uses 360 ms after startup and after every active track.
- Regression gate: pet loading, switching, focus, and prompt tests remain green.
- Operator gate: Ghostty observation confirms idle is visibly slower while
  event animations remain responsive and do not blink.

## Decision

Proceed with the timing-only change described above. Keep the visual gate open
until the operator confirms the perceived cadence in a fresh `lwa` session.
