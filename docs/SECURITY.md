# Security and Spending Controls

## Secrets and first-run credential wizard

- Default secret file: `~/.local/state/lwa-mcp/lwa.env`
- Secret-file mode: `0600`
- State-directory mode: `0700`
- Writes use a same-directory temporary file, `fsync`, and atomic replacement.
- Existing custom environment entries are preserved when the wizard updates recognized provider keys.
- Keys are loaded into the MCP/dashboard process environment without `${...}` interpolation, preserving the exact credential text.
- Dashboard and MCP status endpoints never return secret values.
- The local dashboard can add, replace, and remove recognized provider credentials. It returns only provider names, env names, configured state, and a masked suffix; mutation requests require explicit confirmation and use the same atomic `0600` writer as the credential wizard.
- Provider response bodies and operational errors are redacted before they are
  written to SQLite, returned by the dashboard, or exposed through MCP.
- Structured error fields such as bearer credentials and `api_key`, `token`,
  `secret`, `cookie`, and `authorization` parameters are redacted as well.
- Request and pattern ledgers store SHA-256 prompt hashes rather than prompt bodies.
- Do not place `lwa.env` inside a repository or public synchronization folder.

The installer runs `lwa-router init`, which launches the wizard when standard input is an interactive terminal. A non-interactive installation does not attempt to read from MCP stdio or block a package installation; run `lwa-router keys` afterward.

### Sources checked before prompting

The wizard checks only recognized Lwa provider variables in:

1. An existing Lwa `lwa.env`.
2. The current Codex/process environment.
3. Codex `model_providers.*.env_key` references whose environment variables are currently available.
4. Recognized values or inherited variable names in Codex MCP-server environment configuration.
5. Fixed Codex/current-project files such as `$CODEX_HOME/.env`, `$CODEX_HOME/keys.env`, `$CODEX_HOME/secrets.env`, `.env`, and `.env.local`.

It does not recursively scrape shell history, the home directory, browser stores, system keyrings, or unrelated files. Codex OAuth session data is not copied into Lwa as an API key.

### Intentionally visible input

The wizard uses ordinary echoed `input()` rather than hidden `getpass()` entry. It prints the exact value again before asking whether to save it. This satisfies operator verification but means secrets remain visible in terminal scrollback.

Do not use the wizard while screen sharing, recording the terminal, or allowing untrusted observers. Clear terminal scrollback afterward when appropriate. The wizard does not write credential values to application logs or SQLite.

Re-run it with:

```bash
lwa-router keys
```

## Consent modes

`always_ask` previews every selected model, including free routes.

`paid_only` is the recommended default. It pauses paid and user-pays routes while allowing free/free-quota auxiliary work.

`automatic` is fully automatic. Local caps and caller `allow_paid` flags continue to apply.

The legacy `always` and `never` aliases remain accepted for compatibility, but `always_ask` and `automatic` are the preferred canonical names.

Confirmation tokens are random, HMAC-tagged, process-local, single-use, and expiring. Restarting Lwa MCP invalidates pending tokens.

## Local caps

```yaml
daily_request_cap: 45
monthly_usd_cap: 5.00
```

The router removes exhausted providers before scoring. When dollar cost is unknown, daily request caps are the reliable boundary.

## Tool-library safety

Automatic pattern detection creates prompt recipes, not arbitrary executable code. These recipes pass through the same routing, consent, quota, and ledger controls as direct tasks.

Explicit Python script entries are review-gated:

1. They begin as `draft` and `approved: false`.
2. The source must be inspected before approval.
3. Global `allow_reviewed_script_execution` must also be enabled.
4. Disabling a tool preserves evidence and files for audit.

The library README and manifest are operational metadata. Keep the library path private if tool names or descriptions reveal project details.

## Dashboard exposure

The dashboard binds to `127.0.0.1`. Do not bind it to `0.0.0.0` without authentication, TLS, firewall rules, and a threat review.

The key-management panel is intended only for that local dashboard. It does not revoke keys with providers; deleting a value only removes it from Lwa's managed env file and current process environment. Do not expose the dashboard remotely, and do not paste credentials while screen sharing or recording.

## Single-use preflight tokens

Execution plans and approval tokens are random, signed, memory-only, time-limited, and single-use. Raw prompts and tokens are not stored in SQLite or exposed by the dashboard. Approval only changes `working_may_begin`; a separate plan token is required to execute. If a locked provider fails, the consumed plan cannot reroute or be replayed.
