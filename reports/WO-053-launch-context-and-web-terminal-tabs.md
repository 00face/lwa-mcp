# WO-053 Evidence — Launch Context and Web Terminal Tabs

**Recorded:** 2026-08-21  
**Status:** Partial promotion; implementation and regression gates pass

## Verified

- Installer now creates `~/.local/bin/lwa` and `~/.local/bin/lwa-web` links to
  the active virtual environment and prints a PATH instruction when needed.
- `lwa-web --no-browser` launched from a temporary caller directory emitted a
  URL carrying that directory as encoded `cwd` context.
- Codex sessions validate the context as an existing directory and pass it as
  the PTY child working directory without exposing it in session metadata.
- Broker capacity is eight bounded sessions, enabling multiple tabs while
  retaining cleanup limits.
- LWA-Web now has keyboard-accessible tab controls with selected state, new
  terminal creation, close controls, per-tab output/history, and per-tab PTY
  sockets.
- Live `/codex` serves `terminalTabs` and `newTab` controls.
- Focused launch/tab/accessibility tests: `17 passed`.
- Full non-credential suite: `173 passed, 3 skipped, 2 warnings`.

## Remaining validation

The browser smoke harness verified the live workspace and visual controls, but
an automated click-through of switching two live tabs is not yet included in
the low-resource desktop harness. The implementation is bounded and covered
by static and broker tests; a follow-up visual tab-switch check can be run by
the operator if needed.
