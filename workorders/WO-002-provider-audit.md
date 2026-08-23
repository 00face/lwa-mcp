# WO-002: Provider Adapter Audit

Status: partial; baseline contract, offline adapter coverage, and capability-based image routing complete
Priority: P1

## Objective

Audit all configured provider pipelines against official API behavior without
claiming current models, quotas, balances, or prices from stale seed metadata.

## Scope

- Check capability reporting, timeout, cancellation, retries, error mapping,
  usage extraction, model discovery, quota/balance discovery, and image support.
- Keep unofficial cookie/scraping adapters out of the supported provider set.
- Preserve Puter as `user_pays`.
- Add mocked contract tests per adapter; live tests must be explicit opt-in.

## Acceptance checks

- [ ] Every adapter implements or explicitly rejects each contract capability.
- [ ] Seed metadata is visibly marked fallback metadata.
- [ ] No test makes a paid provider request.
- [ ] Provider failures produce structured, secret-redacted results.
- [x] Shared baseline explicitly rejects unsupported streaming and exposes an
  optional balance probe alias.
- [x] Route input/output limits are enforced by the request model.
- [x] Mocked completion, usage, rate-limit, error-redaction, and provider-matrix
  tests pass without network access.
