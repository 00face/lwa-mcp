# SITREP — LWA Workspace Expansion and Prompt Operations

Date: 2026-08-22
Status: staged; WO-077/078 implementation in progress, WO-079–081 ready

## Current situation

- Codex’s authoritative Stacky cache contains animated PNG frames. The shared
  pet event now exposes bounded animation frames for web/native consumers.
- The web pet is being reduced to approximately 50% of its prior presentation
  size and supports Shift+primary-drag with viewport clamping.
- LWA and Codex output now have explicit Select/Copy controls in addition to
  normal text selection, reducing mouse-selection ambiguity.
- LWA currently has semantic prompt finalization and consensus improvement, but
  lacks a complete editor-assistance layer, a user-controlled ping-pong loop,
  and a dedicated LWA slash-command registry.

## Operational risks and gates

- Ping-pong must be opt-in, bounded by turns/time/tokens, and stop for review;
  it must never recursively submit forever or expose provider secrets.
- Spell correction must be reversible and must not silently alter code,
  paths, commands, quoted text, or user-defined identifiers.
- Autocomplete must be pane-local and screen-reader discoverable.
- Pet animation must remain low-resource and pause when hidden or inactive.

## Sequence

1. WO-077 / TR-077 — animated, movable, bounded pet interaction.
2. WO-078 / TR-078 — deterministic cross-pane selection and copy.
3. WO-079 / TR-079 — LWA prompt editor assistance.
4. WO-080 / TR-080 — opt-in ping-pong consensus loop.
5. WO-081 / TR-081 — LWA-specific slash commands.

## Exit signal

The expansion is complete when all five work orders have automated tests,
accessible keyboard alternatives, redacted status events, bounded resource
behavior, and explicit manual acceptance evidence for mouse and screen-reader
flows.
