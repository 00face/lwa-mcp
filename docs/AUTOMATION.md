# Lwa MCP automation

Lwa maintenance is split between local, no-provider work and explicitly
authorized zero-payload provider probes. The maintenance wrapper uses `flock`,
absolute project paths, bounded entry points, and clear exit codes so a manual
run cannot overlap a scheduled run.

## Local telemetry

The telemetry unit reads the local ledger only:

```bash
scripts/lwa-maintenance.sh telemetry
```

It does not contact providers. The optional user timer writes output to the
systemd journal:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/lwa-mcp-telemetry.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now lwa-mcp-telemetry.timer
journalctl --user -u lwa-mcp-telemetry.service
```

## Explicit provider probes

The live probe checks provider catalog/health endpoints and never submits a
completion prompt. It refuses to run unless the operator supplies an explicit
gate:

```bash
LWA_LIVE_PROVIDER_CHECK=1 scripts/lwa-maintenance.sh live-probe
```

To enable the optional timer, create `~/.config/lwa-mcp/live-check.env` with:

```text
LWA_LIVE_PROVIDER_CHECK=1
# Optional; quota endpoints may consume separate provider limits.
# LWA_LIVE_INCLUDE_QUOTA=1
```

Then install and enable the user units:

```bash
cp systemd/lwa-mcp-live-probe.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now lwa-mcp-live-probe.timer
systemctl --user list-timers lwa-mcp-live-probe.timer
```

Do not enable the live timer merely to make the dashboard look healthy. An
offline `configured` state is intentionally different from `probe_verified`.

## Offline verification

Use the guarded verification entry point for release checks. It runs compile,
test, lint, and wheel validation and does not submit provider completions:

```bash
scripts/lwa-maintenance.sh offline-verify
```

This is intentionally not installed as a frequent timer because dependency
installation and the full test suite are comparatively expensive.

## Safety contract

- Keep provider checks separate from completion execution.
- Keep credentials in the protected Lwa environment file; never put them in
  unit files or command arguments.
- Review `journalctl --user` output for failures and use exit code `75` to
  identify a skipped overlapping run.
- Keep script-tool execution disabled unless its source has been reviewed and
  the project explicitly enables it.
