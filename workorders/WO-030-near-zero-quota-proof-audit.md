# WO-030 - Near-Zero Quota Proof Audit

**Status:** Partial — mechanical audit is implemented; current evidence fails telemetry and stretch gates.
**Priority:** P0
**Parent:** WO-026 through WO-029
**Task rite:** [TR-030](../task-rites/TR-030-near-zero-quota-proof-audit.md)

## Objective

Independently audit whether near-zero live quota usage is proven and whether
the Lwa MCP/LWA Plugin quality bar supports a 10/10 or 11/10 rating.

## Required Evidence

- Two valid live benchmark sessions with complete attribution.
- Authoritative quota denominators and independently recomputable numerators.
- Quality within one point of baseline, zero duplicate execution, and safe
  rollback evidence.
- Clear separation of control-plane overhead from necessary answer tokens.

## Promotion Gate

Award 10/10 only when all mandatory evidence passes. Award 11/10 only when
predictive reuse improves p95 without stale or incorrect answers and the result
survives independent reproduction.

## Rollback

Publish the lower verified score and reopen only the failed bounded order.

## Run Evidence (2026-08-08)

- Added `src/lwa_mcp/audit.py` and `scripts/audit_near_zero_proof.py`.
- Current audit: quota, benchmark, handshake, and safety gates pass; telemetry
  fails because persisted records are unreported/unattributed.
- Current result is non-promoting: `ten_of_ten=false`, `eleven_of_ten=false`.
- Full offline verification: `114 passed`; Ruff clean.
