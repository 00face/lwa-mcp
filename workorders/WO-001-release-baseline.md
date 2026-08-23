# WO-001: Release Baseline and Lifecycle Integrity

Status: complete
Priority: P0
Owner: Lwa MCP maintainers

## Objective

Ship the next compatible Lwa MCP baseline with canonical consent-mode names,
strict preflight ordering, single-use approvals, and auditable reusable-tool
metadata.

## Scope

- Keep `always_ask`, `paid_only`, and `automatic` as canonical values.
- Accept `always` and `never` as compatibility inputs only.
- Verify no provider call occurs during preflight.
- Verify approval tokens expire and cannot be replayed.
- Verify generated tool manifests expose origin, review, and safety state.
- Build source, wheel, ZIP, TAR.GZ, and checksums after dependencies are available.

## Acceptance checks

- [x] Focused lifecycle and token tests pass.
- [x] Static compilation and lint pass.
- [x] Clean-home wheel installation passes with staged dependencies.
- [x] Release artifacts match the release manifest and checksum file.

## Dependencies and blockers

- Verification dependencies were staged in isolated `/tmp` storage.
- Live provider verification remains opt-in and must not use paid requests.
