# Release Manifest — v0.4.1

## Release focus

Lwa MCP v0.4.1 preserves the strict preflight lifecycle so prompt finalization, token budgeting, quota and consent evaluation, consensus topology, and model selection are complete before Lwa-managed provider work begins.

## New execution contract

```text
prepare_task → [approve_preflight] → Working... → run_prepared_task
```

- Specialized MCP task tools now return preflight plans rather than starting provider work.
- `smart_complete` is retained as a preparation-only compatibility alias.
- `confirm_and_run` is retained as an approval-only compatibility alias.
- Consent modes accept the canonical `always_ask`, `paid_only`, and `automatic` names plus the legacy `always` and `never` aliases.
- Tool manifests now record explicit origin, review state, and safety state metadata.
- Plan and confirmation tokens are time-limited, signed, memory-only, and single-use.
- Consensus preflight locks all voter routes, the synthesis route, and the synthesis template.
- Provider failure stops execution with `repreflight_required`; dynamic model switching is forbidden during the active Working phase.
- The CLI prints the full preflight before the literal `Working...` line.
- The dashboard includes a Before Working ledger with route roles, token estimates, locks, approvals, and execution state.

## Security and privacy

- Raw prompts and preflight tokens are not persisted in SQLite.
- The dashboard stores and displays prompt-free preflight metadata only.
- Existing `.env` protection remains `0600`; state/config directories remain `0700`.
- Existing credential values and unrelated `.env` entries remain preserved.

## Validation status

- Python source and test compilation passed with `python3 -m py_compile`.
- Full offline test suite: 25 passed (`pytest -q`).
- Ruff: passed with no findings.
- Dashboard fresh-home import: passed; app reports version `0.4.1`.
- Clean-wheel smoke: passed with the wheel and declared dependencies staged in
  an isolated temporary target; default config installation succeeded.
- Provider contract and matrix coverage: passed with mocked HTTP only; no live
  provider or paid request was made.
- Dependency-free wheel build passed with `python3 -m pip wheel . --no-deps --no-build-isolation`.
- MCP stdio handshake and installed CLI entrypoint execution: not executed.
- Live provider, quota, balance, model-catalog, and billing checks: not
  executed; these require explicit operator credentials and official endpoints.

## Environment limitation

The base interpreter does not include the declared dependencies. Verification
used an isolated dependency target under `/tmp`; no dependencies or provider
credentials were written into the project.

## Artifacts

- `dist/lwa-mcp-0.4.1/` source directory
- `dist/lwa_mcp-0.4.1-py3-none-any.whl`
- `dist/lwa-mcp-0.4.1.tar.gz`
- `dist/lwa-mcp-0.4.1.zip`
- `dist/lwa-mcp-0.4.1-SHA256SUMS.txt`

The three distributable archives pass ZIP/TAR integrity checks and the listed
SHA-256 checksums verify successfully.
