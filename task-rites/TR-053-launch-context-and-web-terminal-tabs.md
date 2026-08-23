# TR-053 — Launch Context and Web Terminal Tabs Rite

**Purpose:** verify directory-independent launch and bounded multi-terminal
behavior in LWA-Web.

**Current result:** Partial promotion. User-bin launch links, encoded caller
context, validated PTY working directories, tab lifecycle code, accessibility
state, and regression tests pass. Live two-tab visual switching remains an
optional follow-up check.

## Action

1. Resolve installed launchers from a temporary caller directory.
2. Launch `lwa-web` with the caller directory encoded as local context.
3. Create, switch, and close multiple browser tabs backed by separate PTYs.
4. Confirm tab controls expose selected state and accessible names.
5. Verify cleanup and run the full non-credential suite.

## Promote when

The launcher context, tab lifecycle, prompt routing, and accessibility checks
pass without leaking paths or prompts into telemetry.

## Rollback

Use one default Codex session and omit the launch-context query while retaining
the existing single-terminal behavior.
