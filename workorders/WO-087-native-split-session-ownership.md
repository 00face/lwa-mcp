# WO-087 — Native Split Session Ownership

Status: partial — native split session/controller and automated routing gates pass; visual Ghostty gate remains
Priority: P0
Dependencies: WO-083, WO-085
Task rite: [TR-087](../task-rites/TR-087-native-split-session-ownership.md)

## Objective

Refactor split-capable launches so LWA owns the left pane and an unmodified
Codex process owns the right pane. The bridge/PTy transcript renderer must not
be used as the visible Codex surface in native split mode.

## Scope

- Add an explicit `native-split` session mode distinct from `bridge-window`.
- Launch Codex directly in the right tmux/Kitty/WezTerm pane.
- Capture and pass the authoritative target pane identity back to LWA.
- Add a pane-targeted controller for reviewed prompt submission, resize, and
  close without injecting LWA text into the Codex prompt prematurely.
- Keep Codex's native slash commands, autocomplete, modals, scrolling,
  selection, pets, graphics, and formatting in the Codex pane.
- Remove the internal Codex feed from the LWA surface when native-split mode
  is active, or replace it with a non-authoritative status/handshake area.
- Retain the existing bridge renderer for approved second-window/fallback
  adapters.

## Acceptance

- In Ghostty/tmux, LWA is visibly left and native Codex is visibly right.
- The right pane's foreground process is Codex, not `lwa_mcp.codex_bridge`.
- LWA consensus output is staged for review and reaches Codex only through an
  explicit send action.
- Codex output never appears duplicated in the LWA pane.
- Pane identity is validated before LWA reports the session ready.
- Missing pane control downgrades to the second-window bridge mode with a
  readable mode explanation.
- Fake terminal tests verify command construction, target identity, routing,
  resize, close, and no prompt leakage.

## Rollback

Disable `native-split` for the affected host and use the existing
`bridge-window` adapter. Do not remove the bridge fallback.
