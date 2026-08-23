# SITREP 011 — Agouti Simulator Lwa End-to-End Reaudit

**Date:** 2026-07-25  
**Status:** Failed end-to-end exercise; lifecycle controls mostly behaved correctly  
**Related work order:** [WO-006](../workorders/WO-006-integration-failure-inoculation.md)

## Situation

The requested exercise was to create or validate a dependency-free,
isometric Conway Game of Life at the workspace location
`/home/face/Documents/Documents/code/agouti_simulator/`, render live cells
as `🐈`, obtain consensus from all eligible free models, make one final pro
coding call, and return control to Codex.

The run exposed a real provider failure and two routing/path quirks. No source
files were changed by this run.

## Evidence ledger

| ID | Expected | Observed | Classification |
|---|---|---|---|
| E-011 | All eligible free/free-quota voters execute and produce consensus. | Preflight selected 15 free/free-quota voters plus synthesis. Execution stopped on the OpenRouter voter with HTTP 401 and `{"error":{"message":"User not found","code":401}}`. | OpenRouter authentication/account failure; consensus incomplete |
| E-012 | A provider failure ends the current Working phase without hidden rerouting. | Lwa returned `repreflight_required`; the consumed plan was not switched in place. | Control success |
| E-013 | The approved reusable Agouti recipe can provide a fallback advisory. | The recipe completed through Groq `openai/gpt-oss-120b`, `free_quota`. | Control success; not equivalent to full consensus |
| E-014 | The final coding stage uses a pro route when requested. | The final call completed through Gemini 2.5 Flash with billing class `free_quota`, even though paid routes were allowed. | Billing/intent mismatch |
| E-015 | The requested absolute target exists before writing. | The operator clarified that the intended target is `/home/face/Documents/Documents/code/agouti_simulator/`; that path exists. The earlier `/code/agouti_simulator/` wording was ambiguous shorthand. | Operator ambiguity; resolved |
| E-016 | The test creates or updates the application. | No files were modified by the test. | Expected handoff behavior; implementation not performed |

## OpenRouter 401 analysis

The failing request was routed to OpenRouter's OpenAI-compatible endpoint. The
repository configuration names the canonical credential `OPENROUTER_API_KEY`,
accepts `OPENROUTER_KEY` as an alias, uses `https://openrouter.ai/api/v1`, and
sends the credential as `Authorization: Bearer <key>`. The observed provider
response was:

```text
OpenRouter HTTP 401: {"error":{"message":"User not found","code":401}}
```

This proves that OpenRouter rejected authentication or account identity. It
does **not** prove which of the following caused it:

1. The test process had no non-empty `OPENROUTER_API_KEY` or
   `OPENROUTER_KEY` value.
2. The configured key was malformed, expired, revoked, or copied incorrectly.
3. The key was validly formatted but associated with an unavailable,
   deleted, disabled, or otherwise unrecognized OpenRouter user/account.
4. The runtime loaded a different environment/configuration than the operator
   expected.

A new API key is therefore **not automatically required**. First verify, without
printing the secret, that the intended process sees a non-empty canonical or
alias variable and that the OpenRouter dashboard still shows the key and its
owning account as active. Replacing the key is warranted only after the current
key is confirmed revoked/expired, the account is unavailable, or the account
owner cannot restore access. If the key is active, correcting environment
loading or configuration is the safer first fix.

Safe local checks should reveal only presence and source metadata, never the
key value. For example:

```sh
test -n "${OPENROUTER_API_KEY:-}" && echo OPENROUTER_API_KEY=present || echo OPENROUTER_API_KEY=missing
test -n "${OPENROUTER_KEY:-}" && echo OPENROUTER_KEY=present || echo OPENROUTER_KEY=missing
```

The next authenticated probe must be a fresh preflight/execution. The failed
plan token must not be reused, and a provider failure must not trigger an
in-Working fallback.

### Dashboard evidence supplied after the run

The operator supplied a dashboard screenshot showing an existing key named
`aistudio 1`, a masked prefix `sk-or-v1-274...2ae`, an unlimited limit, `$0.005`
usage, and last use 23 days ago. This is useful evidence that a key exists on
the account and has been used historically. It does not prove that the current
Lwa process loaded the same secret, that the key is still accepted, or that the
runtime is using the intended environment file. The secret itself is not
recorded here.

## Fixed, still failing, and untested

### Fixed or demonstrated

- Consensus preflight was explicit about its 15 free/free-quota voters and
  synthesis route.
- The locked OpenRouter failure stopped the active phase without hidden
  rerouting.
- A fresh approved recipe completed through Groq.
- A separate final coding handoff completed and returned control to Codex.
- The app's workspace-relative implementation already contains the requested
  isometric canvas and cat-emoji rendering concepts.

### Still failing

- OpenRouter authentication/account access prevents a complete all-free
  consensus result.
- The final coding request did not force or verify a paid/pro billing class.
- The originally reported `/code/agouti_simulator/` path was an operator
  wording ambiguity; the clarified workspace absolute path is resolved.
- The exercise did not perform the requested create/update handoff.

### Untested

- Whether the current OpenRouter key is present, active, revoked, or attached
  to the expected account; the secret was not inspected.
- A successful OpenRouter request after credential remediation.
- A browser smoke test covering console errors, Step, and generation/live-count
  updates.
- A successful paid/pro coding execution.

## Acceptance gates for the next run

- [ ] Fresh OpenRouter preflight and execution return a successful provider
  result; record only credential environment name, provider, model, and status.
- [ ] Consensus execution returns `mode=consensus` with all eligible free
  voters plus synthesis, or records an explicit provider exclusion and reason.
- [ ] The final coding route is explicitly `paid`/pro, not merely
  `allow_paid=true` with a free route winning scoring.
- [x] The clarified workspace absolute path is resolved before any write; the
  original `/code/agouti_simulator/` shorthand is retained only as audit history.
- [ ] Browser smoke verification passes, including Step and live-count changes.
- [ ] The work order records fresh plan IDs, route billing classes, failures,
  and token lifecycle outcomes.

## 2026-07-25 local rite evidence

The local verification rite was run with OpenRouter and Puter explicitly
excluded; the user's OpenRouter credential was not read or displayed.

| Check | Result |
|---|---|
| `node --check code/agouti_simulator/app.js` | PASS |
| `.venv/bin/python -m pytest -q` | PASS: 48 passed, 2 FastAPI deprecation warnings |
| `/home/face/Documents/Documents/code/agouti_simulator/` existence | PASS: present |
| Original `/code/agouti_simulator/` shorthand | ABSENT; resolved as wording ambiguity |
| OpenRouter authenticated retry | FAIL: fresh OpenRouter-only run returned HTTP 401 `User not found` |
| Browser Step/console smoke | STILL UNTESTED |

This closes the local syntax, Python-regression, and clarified-path evidence
only. The dashboard proves a key exists, but the fresh runtime call still
fails authentication, so the OpenRouter, paid-route, and browser gates remain
open.

## Fresh OpenRouter retry result

A new preflight was constrained to `openrouter/openrouter/free` and executed
with the Lwa-managed credential configuration. It returned the same sanitized
error:

```text
openrouter HTTP 401: {"error":{"message":"User not found","code":401}}
```

This narrows the issue: the key is present in the Lwa state file and exists on
the dashboard, but OpenRouter does not currently accept the credential/account
identity presented by the runtime. The next action is to verify the exact
OpenRouter account/key state and refresh the managed credential if necessary;
the secret was not exposed or copied during this run.
