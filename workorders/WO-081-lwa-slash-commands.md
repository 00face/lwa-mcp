# WO-081 — LWA-Specific Slash Commands

Status: ready

## Objective

Provide a dedicated LWA slash-command registry that never collides with
Codex-native commands and exposes follow-up options in the LWA pane.

## Initial command set

- `/lwa help` — list LWA commands and shortcuts.
- `/lwa mode semantic|compact|raw` — choose finalization mode.
- `/lwa providers` — show redacted provider availability.
- `/lwa consensus` — configure or inspect consensus behavior.
- `/lwa pingpong on|off|status` — control the bounded loop.
- `/lwa correct on|off|review` — control spell correction.
- `/lwa template` — browse prompt templates.
- `/lwa clear`, `/lwa undo`, `/lwa redo`, `/lwa debug` — local editor actions.

## Acceptance

- Commands autocomplete only in the LWA prompt and are not forwarded to Codex.
- Follow-up forms/options are keyboard and screen-reader accessible.
- Unknown commands are harmless and explain how to recover.
- Provider/config output is redacted and bounded.

## Validation

Test exact commands, partial commands, arguments, cancellation, mouse options,
keyboard navigation, Codex command isolation, and screen-reader announcements.
