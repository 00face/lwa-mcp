# WO-093 — Smooth Single-Pet Animation Loop

Status: Implementation complete; visual acceptance open

## Problem

The C same-ID animation path visibly animates, but the operator reports two
pet images and a blink when the animation cycle restarts. This indicates stale
image IDs are surviving across protocol experiments and that the loop boundary
still performs a visually disruptive frame replacement.

## Objective

Render exactly one pet instance and loop its animation continuously without a
blank frame, duplicate image, cursor coupling, or prompt contamination.

## Required invariants

- One owned image identity per native LWA session.
- All stale test image IDs are deleted before the active pet is placed.
- Frame 0 is loaded once; loop playback never reinitializes the image.
- A loop transition must not emit a delete or clear operation.
- LWA never injects a second pet while Codex owns a native pet instance.

## Acceptance gates

1. **Single-instance gate:** only one visible pet remains after a fresh launch,
   `/pets`, resize, and animation restart.
2. **Frame gate:** every frame hash in the selected animation is reached.
3. **Loop gate:** observe two complete cycles with no blank frame or visible
   restart blink.
4. **Placement gate:** the pet remains at the Codex pane’s bottom-right.
5. **Input gate:** no graphics protocol text, hashes, or frame IDs reach either
   prompt.
6. **Fallback gate:** unsupported graphics hosts still show one text pet.

## Stop condition

Do not add another animation protocol. If the loop gate fails, capture the
exact image IDs and transition sequence, then fix lifecycle/cleanup or frame
timing in the selected C path.
