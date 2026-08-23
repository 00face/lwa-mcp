# WO-053 — Launch Context and Web Terminal Tabs

**Status:** Partial — launcher context, user-bin links, bounded tab sessions,
and accessible tab controls are implemented and regression-tested. A live
two-tab visual switch check remains optional follow-up validation.
**Evidence:** [WO-053 evidence](../reports/WO-053-launch-context-and-web-terminal-tabs.md)
**Parent:** WO-052
**Task rite:** [TR-053](../task-rites/TR-053-launch-context-and-web-terminal-tabs.md)

## Objective

Allow installed `lwa` and `lwa-web` commands to run from any caller directory,
and provide multiple switchable Codex PTY tabs in LWA-Web.

## Contract

- Launchers preserve the caller's working directory for Codex.
- `lwa-web` carries the caller directory into the local dashboard through a
  validated launch context; it never trusts arbitrary non-directory paths.
- Each web tab owns a separate bounded PTY session and can be closed without
  affecting other tabs.
- Tab controls are keyboard reachable, named, and expose selected state to
  assistive technology.
- Session and tab metadata remain non-sensitive.

## Acceptance

- `lwa` and `lwa-web` resolve from PATH outside the repository.
- A web launch from directory A starts Codex in A; a second tab can start in B.
- Switching tabs restores each tab's terminal output and prompt surface.
- Closing one tab reaps only its PTY.
- Focused broker, launch-context, and accessibility tests pass.
