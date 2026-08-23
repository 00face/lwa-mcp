# WO-089 Visual Acceptance Evidence

Status: partial — primary layout gate passed; feature-interaction subchecks remain
Related work order: [WO-089](../workorders/WO-089-native-split-visual-acceptance.md)
Related task rite: [TR-089](../task-rites/TR-089-native-split-visual-acceptance.md)

## Evidence

Operator screenshot received after the native split refactor.

Observed:

- LWA occupies the left pane.
- Native Codex occupies the right pane.
- LWA reports `Native Codex pane connected (%1)`.
- The right pane displays the Codex prompt and model/directory status.
- The right pane no longer displays the `lwa_mcp.codex_bridge` traceback.
- LWA's left pane no longer duplicates the Codex transcript.
- The tmux session is visibly split into the expected LWA/Codex ownership model.

## Remaining visual subchecks

- Slash-command autocomplete and modal placement.
- Native Codex scrolling and mouse selection/copy.
- Pet animation, sizing, and graphics rendering.
- Ctrl+C once-to-interrupt and twice-to-exit behavior in the fresh layout.

