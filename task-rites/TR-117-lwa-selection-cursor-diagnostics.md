# TR-117 — LWA selection and cursor diagnostics

1. Add metadata-only trace helpers with a strict no-content contract.
2. Trace cursor-owner changes, normalized navigation keys, and mouse phases.
3. Trace LWA selection anchor, drag, and release lengths without text.
4. Add unit coverage for classification and trace throttling/shape.
5. Run C01–C07 automatically where possible, then lint and the full suite.
6. Leave C08–C20 as operator gates requiring Ghostty/tmux observation and
   record the resulting evidence in the next SITREP.

## Rite completion rule

This rite is complete when the logs can identify the failing ownership layer;
it is not complete merely because the process starts or tests pass.

