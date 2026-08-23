# Lwa MCP Operator Quick-Start

## Install and initialize

```bash
./scripts/install.sh
./.venv/bin/lwa-router doctor
```

For unattended setup, use:

```bash
./scripts/install.sh --no-key-wizard
```

Use `--with-dev` for test dependencies or `--venv PATH` for a separate
environment. On Windows, run `scripts\\install.bat`; the installed launchers
are `lwa.exe` and `lwa-web.exe` inside the virtual environment.

The installer creates the virtual environment and XDG config/state/data
locations. On an interactive terminal, `lwa-router init` starts the visible
credential wizard. Re-run credentials with:

```bash
./.venv/bin/lwa-router keys
```

The wizard recognizes `GEMINI_API_KEY` (and the `GOOGLE_API_KEY` alias) for
Google Gemini and `OPENAI_API_KEY` (and the `CHATGPT_API_KEY` alias) for the
OpenAI/ChatGPT API. Both are stored in the protected environment file.

The official OpenAI media routes use the same `OPENAI_API_KEY`. Image output
is saved locally; video generation is asynchronous and downloads the completed
MP4 into the Lwa state `generated` directory. Both remain paid routes.

If setup was previously marked complete but a required key is empty, the next
`init` run continues and asks for the missing entry. To replace an existing
key that a provider rejects, run:

```bash
./.venv/bin/lwa-router keys --retry-configured
```

The secret file is `~/.local/state/lwa-mcp/lwa.env` (`0600`); its containing
state directory is `0700`. Credential values are preserved literally.

## Register Codex and open the dashboard

Register the installed entry point in Codex:

```toml
[mcp_servers.lwa]
command = "/absolute/path/lwa-mcp/scripts/codex-mcp-entrypoint.sh"
```

The Codex launcher starts the loopback dashboard automatically and emits its
URL on startup. Codex workflows are exposed through the packaged `$lwa`,
`$lwa-plan`, `$lwa-sitrep`, and `$lwa-doctor` skills. Native Codex commands
such as `/skills` and `/model` remain unchanged. The dashboard URL is a CLI
operation: `./.venv/bin/lwa-router doctor --show-dashboard-url`. If you want
to start it manually:

```bash
./scripts/run-dashboard.sh
```

Default URL: `http://127.0.0.1:8766`. Keep it on loopback unless an
authenticated, encrypted reverse proxy is in place.

The existing Observatory is `/`; the additive framed Codex workspace is
`/codex`. It is PTY-backed and uses a bounded canvas renderer so it remains
usable on low-resource Linux systems. The LWA Prompt and direct Codex Prompt
are both available in the frame.

## Safe task execution

Use the strict sequence:

```text
prepare_task → approve_preflight (if required) → run_prepared_task
```

Inspect the provider, model, token budget, consent, route locks, and
`working_may_begin` before execution. A provider failure requires a new
preflight; Lwa does not switch models during active work.

The request syntax is canonical and case-sensitive. `task` must be one of the
`TaskKind` values exposed by CLI help or `syntax_contract_resource`; it is not
a free-form description. `quality` is one of `economy`, `balanced`, or `high`.
For example:

```text
task=query
quality=economy
```

Use `build_consensus` for consensus, `generate_image` for image generation,
and `generate_video` for video generation; do not route those through a
generic text request. Invalid syntax is rejected before a provider route or
plan token is created.

The canonical consent modes are `always_ask`, `paid_only`, and `automatic`.
Legacy `always` and `never` inputs remain compatibility aliases. Local daily
request and monthly dollar caps remain enforced in every mode.

## Reusable tools

Search and inspect before rebuilding recurring work:

```text
suggest_library_tools → read_library_tool → run_library_tool
```

Record validated recurring work with `observe_workflow`. Script tools begin as
drafts and require source review, explicit approval, and the global
`allow_reviewed_script_execution` setting before execution.

## Backup and recovery

Back up these paths while Lwa is stopped:

```text
~/.config/lwa-mcp/router.yaml
~/.local/state/lwa-mcp/lwa.env
~/.local/state/lwa-mcp/lwa.sqlite3
~/.local/share/lwa-mcp/tool-library/
```

To migrate from the previous Castor & Pollux namespace, run:

```bash
./scripts/migrate-from-castor-pollux.sh
```

Migration is non-destructive. Use `--force` only when replacement is intended;
the existing destination is backed up with a timestamped
`.pre-migration-*` suffix first. Restore a backup by stopping Lwa and copying
the desired file back into its original path, preserving `0600` for `lwa.env`
and `0700` for private directories.

## Troubleshooting

- Run `lwa-router doctor` after changing credentials or configuration.
- Missing keys leave providers visible but unselectable; run `lwa-router keys`.
- Refresh live catalogs only when network access and provider credentials are
  intentionally available.
- Treat seed models, quotas, balances, prices, and billing as fallback data
  until confirmed by an official endpoint.
- If a route fails, prepare again; do not retry a consumed plan token.
- If the dashboard port conflicts, set `dashboard_port` in the router YAML.

## Verification scripts

Run the complete dependency-backed offline verification in an isolated
environment:

```bash
./scripts/verify-offline.sh
```

The script installs the declared development dependencies, runs compilation,
pytest, Ruff, and a dependency-free wheel build. Set `LWA_VERIFY_ENV_DIR` to
reuse a verification environment or pass `--keep-env` while investigating a
failure.

After installation, verify the MCP stdio handshake and discoverability:

```bash
./.venv/bin/python scripts/check-mcp-handshake.py
```

Run live model-catalog checks explicitly. This performs catalog/health probes,
never completion requests, and refuses to run without the opt-in flag:

```bash
LWA_LIVE_PROVIDER_CHECK=1 ./scripts/verify-live-providers.sh
LWA_LIVE_PROVIDER_CHECK=1 ./scripts/verify-live-providers.sh --quota
```

Quota mode calls only configured official quota/balance endpoints. Provider
freshness claims remain limited to the returned endpoint evidence.

## Uninstall

Stop the MCP server and dashboard, then remove the checked-out project and its
virtual environment if no longer needed. User state is separate and is not
removed automatically:

```bash
rm -rf /path/to/lwa-mcp/.venv
```

Before removing user state, preserve or manually remove the following only when
the operator intends to discard credentials, ledger history, and reusable tools:

```text
~/.config/lwa-mcp/
~/.local/state/lwa-mcp/
~/.local/share/lwa-mcp/
```
