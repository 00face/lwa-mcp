# TR-084 — Second-Window Terminal Adapters Rite

Status: complete

Execute after TR-082; use TR-083 results to define split-to-window downgrade.

1. Add fake launcher fixtures for Alacritty, Tabby, Wave, GNOME Terminal,
   Konsole, Terminator, and Guake.
2. Verify argv-level quoting and working-directory handling with spaces,
   Unicode, and project paths.
3. Verify bridge readiness, current-terminal LWA readiness, bidirectional
   input/output, resize, cancellation, and child/window exit.
4. Verify redacted diagnostics, accessible status announcements, and no raw
   secrets in transcripts or logs.
5. Exercise low-resource text mode and independently report graphics,
   Sixel, Kitty, mouse, and clipboard capabilities.
6. Record one evidence row per terminal and promote only passing adapters.

Result: all seven named window adapters pass argv-level fake-launcher tests;
desktop visual inspection is separately recorded as an operator gate.
