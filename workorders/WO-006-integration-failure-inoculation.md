# WO-006: Integration Failure Inoculation

Status: in progress; consensus voter-policy remediation implemented, remaining gates open
Priority: P1

## Objective

Turn the Agouti Simulator Lwa integration exercise into regression coverage for
route-policy, provider-capability, token-lifecycle, path-resolution, and
runtime-verification failures.

## Incident scope

- Lwa auxiliary routing and consensus preflight/execution lifecycle.
- The originally stated `/code/agouti_simulator` shorthand was clarified by
  the operator as `/home/face/Documents/Documents/code/agouti_simulator/`.
- The browser app's verification boundary: `node --check` passed, but no
  browser-level check was run.

## Evidence-based failure ledger

| ID | Expected | Observed | Classification |
|---|---|---|---|
| F-001 | Library search accepts a valid task kind. | Invalid values were rejected until `TaskKind` was inspected; `coding_aux` and `document_editing` are the valid enum values used afterward. | Operator/API discoverability gap |
| F-002 | A consensus request produces a consensus plan. | Generic `prepare_task` selected one paid primary route; the specialized `build_consensus` tool was needed. | Wrong tool/intent mapping |
| F-003 | `allow_paid=false` excludes paid and user-pays voters. | The consensus preflight still listed a Puter `user_pays` voter. | Policy-filtering defect; remediated in current rite |
| F-004 | Locked routes execute with compatible request parameters. | Puter rejected `temperature` with HTTP 400; Lwa returned `repreflight_required` and stopped work. | Provider capability mismatch |
| F-005 | A ready plan token can be used once within its lifecycle. | A reported-ready fallback token was rejected as expired/used; a fresh preflight was required. | Token lifecycle/observability gap |
| F-006 | Free fallback provides a usable advisory route. | Groq `free_quota` completed successfully. | Control success |
| F-007 | An approved pro route executes when credentials are valid. | ZenMux/Gemini execution returned HTTP 403 `access_denied`; no pro result was produced. | Credential/provider access failure |
| F-008 | An absolute target path is available before implementation. | `/code/agouti_simulator` was absent; the app was created at workspace-relative `code/agouti_simulator`. | Path contract mismatch |
| F-009 | Syntax and browser behavior are verified. | `node --check code/agouti_simulator/app.js` passed; browser-level verification was skipped. | Verification gap |
| F-010 | All eligible free voters complete a consensus run. | The all-free plan selected 15 voters plus synthesis, but the OpenRouter voter returned HTTP 401 `User not found`; the plan stopped with `repreflight_required`. | OpenRouter authentication/account failure |
| F-011 | A requested final pro coding call uses a pro route. | The final coding call completed through Gemini 2.5 Flash with billing class `free_quota` despite `allow_paid=true`; no paid/pro route was forced. | Billing intent/scoring mismatch |
| F-012 | The requested absolute target path is available before implementation. | The clarified target `/home/face/Documents/Documents/code/agouti_simulator/` exists; the earlier `/code/agouti_simulator/` wording was shorthand ambiguity. | Resolved operator ambiguity |
| F-013 | An existing OpenRouter key is available to the runtime. | Dashboard screenshot shows key `aistudio 1`, masked prefix `sk-or-v1-274...2ae`, unlimited limit, `$0.005` usage, last used 23 days ago. | Account evidence present; runtime authentication still unverified |

The ledger records the observed tool responses and filesystem state. It does
not claim that a consensus result or pro coding handoff was produced.

## Inoculation actions

1. Add a task-kind discovery/validation test covering every `TaskKind` enum
   value and a clear error for unknown values.
2. Add a consensus contract test proving that the generic path cannot silently
   downgrade a consensus request to `mode=single`.
3. Add a billing-policy test proving that `allow_paid=false` excludes both
   `paid` and `user_pays` routes, or explicitly documents why a class is exempt.
4. Add provider capability metadata and preflight validation for unsupported
   parameters such as `temperature`; reject before provider execution when the
   route cannot accept them.
5. Preserve the strict token rule: never reuse a consumed or rejected token and
   never auto-switch during Working. A `repreflight_required` result must end
   the current Working phase and require a new preflight.
6. Add a preflight-to-execution correlation check so a plan reported ready but
   rejected as expired/used is surfaced as a lifecycle defect with plan ID,
   without exposing secrets.
7. Check target paths before writing. Resolve the requested absolute path and
   report `implementation_path_not_found` instead of silently changing the
   requested location; only use a workspace-relative fallback after explicit
   operator confirmation.
8. Add a browser smoke test that loads the app, checks for console errors,
   clicks Step, and confirms generation/live-count updates. Keep syntax checks
   as a separate gate.
9. Record provider 403s as access failures, not successful pro handoffs; retry
   only through a new approved preflight after credentials or provider state
   changes.
10. Treat OpenRouter's `401 User not found` as an authentication/account
    diagnostic, not proof that a new key is required. Check non-empty
    `OPENROUTER_API_KEY`/`OPENROUTER_KEY` presence without printing secrets,
    then verify key and account state in OpenRouter. Replace the key only when
    it is revoked/expired or the account cannot be restored.
11. Add a route-intent assertion for pro requests: `allow_paid=true` permits a
    paid route but does not require one. A pro handoff must either require a
    paid billing class in the request or fail clearly when no paid route is
    available.
12. Preserve the clarified absolute path contract:
    `/home/face/Documents/Documents/code/agouti_simulator/`. Keep the original
    `/code/agouti_simulator/` wording only as historical audit evidence.

### Implemented in this rite

- `prepare_consensus` now enumerates all eligible `free` and `free_quota`
  providers instead of honoring the arbitrary voter cap.
- Consensus requests explicitly set `allow_user_pays=False`.
- A non-free decision during voter construction raises a policy violation
  before the plan is created.
- Regression coverage now proves all configured free voters are included and a
  configured user-pays model is excluded.

## Acceptance tests

- [ ] `suggest_library_tools` accepts all current `TaskKind` values and gives a
  bounded error for unknown values.
- [ ] A consensus request returns `mode=consensus` and at least one voter plus
  a synthesis route.
- [x] A no-paid consensus plan contains zero `paid` or `user_pays` voter routes.
- [ ] Unsupported provider parameters are rejected before execution.
- [ ] A consumed/expired plan token cannot execute and returns a clear
  re-preflight instruction.
- [ ] A provider failure stops Working without hidden rerouting.
- [ ] The requested implementation path is checked before any file write.
- [ ] The Agouti app passes syntax and browser smoke verification.
- [ ] OpenRouter credential presence/account state is diagnosed without
  exposing the secret, and a fresh authenticated run succeeds.
- [ ] A pro coding request either executes with `billing_class=paid` or
  returns an explicit no-paid-route result; `allow_paid=true` alone is not
  sufficient evidence.
- [ ] SITREP status is not promoted to ready until every applicable check is
  green and the pro route, if requested, actually returns a result.

## 2026-07-25 local rite evidence

Run with OpenRouter and Puter excluded; no OpenRouter secret was inspected.

| Check | Result | Gate impact |
|---|---|---|
| `node --check code/agouti_simulator/app.js` | PASS | Syntax portion demonstrated; browser portion remains open |
| `.venv/bin/python -m pytest -q` | PASS: 48 passed, 2 deprecation warnings | Local regression evidence green |
| `/home/face/Documents/Documents/code/agouti_simulator/` | PRESENT | Clarified absolute-path gate demonstrated |
| Original `/code/agouti_simulator/` shorthand | ABSENT | Resolved as operator wording ambiguity |
| Dashboard key evidence | PRESENT, secret not recorded | Runtime authentication still open |
| OpenRouter-only retry | FAIL: HTTP 401 `User not found` | Dashboard key exists, but runtime credential/account authentication remains unresolved |
| Browser Step/console smoke | NOT RUN | Browser gate remains open |

The Python test command is intentionally run from the existing project virtual
environment; the system Python lacks the project's pytest and runtime
dependencies. No source files were changed by this rite.

The fresh OpenRouter-only preflight was constrained to
`openrouter/openrouter/free` and used the Lwa-managed credential configuration.
It returned HTTP 401 `User not found` again. This confirms a runtime
authentication/account problem remains even though the dashboard shows an
existing key; it does not by itself prove that a replacement key is required.

## Exit criteria

Close WO-006 only after the acceptance tests are automated or explicitly
waived, a fresh end-to-end run records provider/model/billing/plan outcomes,
and a new SITREP separates fixed, still failing, and untested controls.
