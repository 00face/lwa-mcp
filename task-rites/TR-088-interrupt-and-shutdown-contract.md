# TR-088 — Interrupt and Shutdown Contract Rite

Status: partial — automated interrupt, clean-exit, and signal conversion gates pass

Execute after TR-087.

1. Add a small, testable interrupt state machine: idle, interrupt-sent,
   exiting, and closed.
2. Route the first interrupt only to the active Codex session/controller.
3. Route a repeated interrupt within the grace interval to LWA shutdown.
4. Normalize SIGINT/SIGTERM/EOF handling in the bridge and launcher and
   suppress expected cancellation tracebacks.
5. Assert terminal restoration after every exit path, including cancelled
   consensus and failed pane attachment.
6. Add fake-process tests for process-group cleanup, socket cleanup, and
   repeated Ctrl+C behavior.
7. Perform a manual Ghostty check confirming one interrupt and one clean exit
   sequence.
