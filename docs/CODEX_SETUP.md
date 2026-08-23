# Codex Integration

## Install and initialize

```bash
cd /absolute/path/lwa-mcp
./scripts/install.sh
# The visible-input key wizard runs automatically.
./.venv/bin/lwa-router doctor
```

The first interactive installation checks recognized values inherited by Codex, Codex provider `env_key` references, Codex MCP environment maps, and recognized `.env` files before asking for missing values. The wizard intentionally echoes pasted values and prints the exact value again for confirmation.

Re-run credential setup with:

```bash
./.venv/bin/lwa-router keys
```

Missing credentials do not crash the server. Unconfigured providers remain visible but cannot be selected. Codex OAuth session data is not treated as a reusable third-party API key.

## Register Lwa MCP

```toml
[mcp_servers.lwa]
command = "/absolute/path/lwa-mcp/scripts/codex-mcp-entrypoint.sh"
```

## Launch Lwa from terminal or web

Lwa provides two operator-facing launch surfaces. Install the project into its
virtual environment first; the package exposes `lwa` and `lwa-web` commands.

```bash
# Start the terminal surface and launch Codex inside the Lwa frame.
lwa

# Start the local web surface and open the browser.
lwa-web

# Useful for remote/headless terminals.
lwa-web --no-browser
```

If the environment has not been installed yet, run `./scripts/install.sh`.
For a noninteractive install, use `./scripts/install.sh --no-key-wizard`.

The repository also includes direct launchers for installations that are not
on `PATH`:

```bash
./scripts/lwa.sh
./scripts/lwa-web.sh
```

On Windows, run `scripts\\lwa.bat` or `scripts\\lwa-web.bat`. The launchers
start the localhost Lwa dashboard before handing control to Codex or opening
the browser. Use `codex` directly whenever the Lwa frame is not wanted.

The browser surface is served by Lwa; there is intentionally no standalone
`index.html` launch path. This keeps the browser connected to the local Lwa
session service and avoids relying on `file://` browser behavior.

The existing Observatory dashboard remains available at `/`. The framed Codex
workspace is an additive `/codex` route with a PTY-backed graphical terminal,
Codex Feed, Codex Prompt, LWA Feed, and LWA Prompt. Low Resource mode is on by
default; it bounds terminal history and disables shader animation until the
operator enables it.

The launcher starts the MCP server without waiting for the auxiliary dashboard,
which keeps Codex startup bounded. Set `LWA_MCP_START_DASHBOARD=1` to start
the dashboard from the same launcher, or run `./scripts/run-dashboard.sh`
separately. The launcher also
falls back to `/tmp/lwa-mcp-codex` for the database and tool library when the
normal home-state path is not writable, while still reading the real router
config and env file.

The Codex plugin exposes explicit skills: `$lwa` for orchestration,
`$lwa-plan` for preparation, `$lwa-sitrep` for evidence-backed reporting, and
`$lwa-doctor` for diagnostics. Native Codex commands such as `/skills` and
`/model` remain unchanged. The repository's dashboard CLI remains available as
`./.venv/bin/lwa-router doctor --show-dashboard-url`; it is not a Codex plugin
slash command and is not copied into user-global command or prompt directories.

## Suggested Codex doctrine

```text
Use Lwa MCP for quota-aware auxiliary work: conversation compression, prompt optimization,
document editing, SITREPs, planning, consensus, verification, narrow coding support, and quick queries.

When work resembles a recurring prior workflow, call suggest_library_tools first. Inspect a candidate
with read_library_tool and use run_library_tool only when its task, description, and triggers match.
After a recurring workflow succeeds and is validated, call observe_workflow with a stable name,
concrete description, project, and tags. Never approve a script tool without reviewing its source.

Before displaying or writing `Working...`, call `prepare_task` or the specialized task tool. The
returned preflight must show `working_may_begin=true`. When it requires approval, call
`approve_preflight`; this only unlocks the plan. Then display `Working...` and call
`run_prepared_task`. Never route, optimize, plan consensus, or switch models after execution starts.
When a route fails, stop Working and perform a new preflight. Set `allow_paid=false` unless premium
escalation is materially justified.
```

## Strict phase sequence

```text
1. prepare_task / specialized preparation tool
2. approve_preflight, only when required
3. verify working_may_begin=true
4. display Working...
5. run_prepared_task
```

`smart_complete` and `confirm_and_run` remain as compatibility names but are preparation/approval aliases in v0.4; neither begins provider execution. A host-owned Codex spinner may still appear while Codex itself is processing because MCP cannot control the host shell.

The preferred consent-mode names are `always_ask`, `paid_only`, and `automatic`. Legacy `always` and `never` strings remain accepted for compatibility.

## Model-switch modes

```text
set_switch_confirmation("always_ask")
set_switch_confirmation("paid_only")
set_switch_confirmation("automatic")
```

The selected mode is stored in SQLite and can be changed in the dashboard.

## Persistent library paths

```text
Config:        ~/.config/lwa-mcp/router.yaml
Secrets:       ~/.local/state/lwa-mcp/lwa.env
Ledger:        ~/.local/state/lwa-mcp/lwa.sqlite3
Tool library:  ~/.local/share/lwa-mcp/tool-library
Catalog:       ~/.local/share/lwa-mcp/tool-library/CATALOG.md
Dashboard:     http://127.0.0.1:8766
```

## Migration from the prior baseline

```bash
./scripts/migrate-from-castor-pollux.sh
```

The migration copies old configuration and state without deleting the source files.
Migration creates destination config and state directories with mode `0700` and
applies mode `0600` to the copied environment file. Existing destination files
are preserved unless `--force` is supplied; forced replacements receive a
timestamped `.pre-migration-*` backup first.
