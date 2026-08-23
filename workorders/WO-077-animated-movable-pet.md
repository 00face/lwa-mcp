# WO-077 — Animated and Movable Codex Pet

Status: complete — animated Codex frames and bounded Shift-drag implemented

## Objective

Render the authoritative Codex pet animation at an appropriate low-resource
size and permit Shift+primary-drag repositioning without intercepting ordinary
terminal input.

## Acceptance

- Uses Codex-owned frame identity; no replacement sprite.
- Animation is bounded, pauses when inactive/hidden, and does not duplicate
  timers across tabs or reconnects.
- Default presentation is approximately 50% of the previous size.
- Shift+drag moves the pet within the terminal viewport; ordinary click/drag
  remains available for normal selection.
- Keyboard Shift+arrow movement and an accessible status announcement provide a
  non-drag alternative.

## Validation

Test frame discovery, animation bounds, timer cleanup, drag clamping, keyboard
movement, tab isolation, resize, and low-resource mode.

## Evidence

Codex’s local Stacky cache currently resolves to 12 bounded frames. Web
animation uses a 120ms timer, renders at 96×104 CSS pixels, and supports
Shift+primary-drag with pointer capture and viewport clamping. The status text
exposes the keyboard/mouse affordance without exposing payloads.
