# WO-094 — Pet Track Loading and Atomic Switching

Status: Implementation complete; visual acceptance open
Priority: High

## Problem

The authoritative Codex pet cache contains ordered frames for multiple visual
states, but LWA currently infers tracks inside the terminal loop. The idle
track is being melded with welcome and completion animations, and switching
pets can crash the native frame instead of replacing the active pet safely.

## Objective

Load each configured pet as a validated playback state with distinct idle,
welcome, action, and completion tracks. Trigger non-idle tracks only from
explicit LWA/Codex events, and switch pets atomically without crashes,
duplicates, stale frames, or prompt contamination.

## Required behavior

- Idle playback uses only the authoritative idle track and loops continuously.
- Welcome playback runs once when a pet is first loaded, then enters idle.
- Action playback runs only after an explicit event such as prompt submission,
  tool activity, or Codex response, then returns to idle.
- Completion playback runs once after a successful LWA/Codex task, then returns
  to idle.
- Transparent timing frames hold the previous visible frame.
- A pet switch prepares and validates the complete candidate before changing
  the active pet.
- A failed switch retains the current pet and reports a redacted error.
- Exactly one LWA-owned native image identity is visible after every switch.
- Unsupported terminals retain the text fallback and never receive graphics
  protocol bytes.

## Implementation requirements

1. Create an immutable `PetPlaybackState` containing identity, source,
   normalized frames, track ranges, current track, frame index, generation,
   and placement signature.
2. Move track classification out of `terminal_frame.py` and make the loader
   authoritative for idle/welcome/action/completion tracks.
3. Add a bounded event queue with cooldown and cancellation semantics so a new
   event cannot corrupt an active action track.
4. Implement candidate-first, atomic pet switching with generation checks.
5. Keep image cleanup and placement tied to the active generation only.
6. Add crash-safe diagnostics to the existing LWA debug log without exposing
   credentials or image payloads.

## Acceptance gates

1. **Track separation:** idle, welcome, action, and completion frames are
   distinct and unit-testable for every cached pet.
2. **Idle gate:** idle does not enter welcome or completion frames during ten
   minutes of inactivity.
3. **Trigger gate:** each supported event fires its designated track exactly
   once and returns to idle.
4. **Switch gate:** switching across all available cached pets succeeds five
   consecutive times without a crash or stale frame.
5. **Failure gate:** invalid, missing, corrupt, and partially readable pets do
   not terminate LWA and leave the previous pet visible.
6. **Generation gate:** an old animation callback cannot place frames after a
   switch completes.
7. **Visual gate:** one pet remains correctly placed and no blink or duplicate
   appears during load, action completion, resize, or switch.
8. **Input gate:** no Kitty protocol, hashes, base64, or image IDs enter either
   prompt.
9. **Fallback gate:** text-only hosts remain functional.

## Stop condition

Do not add more frame timing constants to the terminal loop. If the cache does
not expose authoritative track metadata, record the limitation and keep the
classification isolated in the pet loader so it can be replaced without
another terminal refactor.
