# TR-087 — Native Split Session Ownership Rite

Status: partial — automated launch, pane identity, payload, resize, and cleanup gates pass

Execute after TR-083 and TR-085.

1. Define a typed launch/session contract with `native-split` and
   `bridge-window` as separate modes.
2. Build fake tmux, Kitty, and WezTerm executables that return pane IDs and
   record every command sent to the target pane.
3. Launch a direct Codex child in the right pane and assert that the bridge
   supervisor is not the visible foreground process.
4. Verify LWA draft → consensus → review → explicit send routing. Assert that
   no draft or consensus text reaches Codex before the send action.
5. Verify native Codex slash commands, modals, autocomplete, scrolling,
   mouse selection, copy, graphics, and pets remain in the right pane.
6. Verify resize, Codex exit, pane close, LWA exit, and failed handshakes do
   not leave orphaned processes or sockets.
7. Run the existing second-window tests to prove the fallback behavior remains
   unchanged.

Required evidence: automated routing report, process-tree assertion, pane-ID
handshake trace, and one operator screenshot matching the expected layout.
