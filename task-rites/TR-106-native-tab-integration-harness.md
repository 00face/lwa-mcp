# TR-106 — Native Tab integration rite

1. Start a private tmux server with two deterministic shell panes.
2. Install the production binding helper against those panes.
3. Send alternating Tab events from each pane.
4. Assert exact receiver bytes and active-pane identity.
5. Repeat 100 cycles and test stale copy-mode cancellation.
6. Tear down the private server in every exit path.
