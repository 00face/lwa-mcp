# WO-089 — Native Split Visual Acceptance

Status: partial — primary left/right pane placement passed; modal, selection, pet, graphics, and interrupt subchecks remain
Priority: P0
Dependencies: WO-087, WO-088
Task rite: [TR-089](../task-rites/TR-089-native-split-visual-acceptance.md)

## Objective

Prove that the forged native split is visually understandable and that each
surface owns the controls and output assigned to it.

## Expected layout

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ LWA — prompt pipeline                    CODEX — native terminal           │
│                                                                          │
│ LWA feed / consensus history          Codex feed, slash menus, modals     │
│                                                                          │
│ LWA Prompt                             Codex Prompt                        │
│ > draft and review text                > native Codex input                │
│                                                                          │
│ Tab: focus pane · Enter: submit LWA · Alt+Enter: send reviewed Codex     │
└──────────────────────────────────────────────────────────────────────────┘
```

The right surface must look and behave like standalone Codex. A Python
traceback, bridge status stream, duplicated Codex transcript, or hidden modal
in the LWA pane is a failure.

## Acceptance

- LWA remains left and Codex remains right after startup, resize, and prompt
  submission.
- Codex slash-command follow-ups and permission modals appear below/within
  the Codex prompt in the right pane.
- LWA status and consensus messages remain confined to the left pane.
- Mouse selection, copy, keyboard focus, and screen-reader labels match the
  owning pane.
- No flicker, duplicated text, oversized/static pet, bridge traceback, or
  cursor ownership ambiguity is visible.
- Capture before/after screenshots and record terminal, dimensions, renderer,
  and selected launch mode.
