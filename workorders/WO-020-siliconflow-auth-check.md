# WO-020 — SiliconFlow Credential Mapping and Model Check

**Status:** complete; diagnostic result recorded, provider remains unhealthy  
**Priority:** P1  
**Parent:** WO-017 / Rite 10

## Objective

Verify which environment variable supplies the SiliconFlow credential and run
one authorized, redacted `GET /v1/models` check. Do not print, rotate, replace,
or persist the credential.

## Evidence boundary

- The configured endpoint is `https://api.siliconflow.cn/v1/models`.
- SiliconFlow's official contract requires `Authorization: Bearer <token>`.
- The observed HTTP 401 is therefore an authentication/account-state failure
  class, not evidence that the endpoint path is wrong.

## Scope

1. Inspect configuration and process environment names only; report the name,
   not the value.
2. Confirm whether the expected variable is non-empty, without revealing
   length, prefix, hash, or secret material.
3. With explicit operator authorization, issue one bounded `GET /v1/models`.
4. Record only HTTP status, safe error code/message, content type, and model
   count when successful.
5. Keep all completion calls, paid routes, and user-pays routes disabled.

## Acceptance

- [ ] Credential environment-variable mapping is documented without disclosure.
- [ ] Authorized request result is redacted and reproducible.
- [ ] 401/403/429/5xx outcomes remain unhealthy and do not route stale seeds.
- [ ] No key rotation, endpoint rewrite, or billing change occurs.

## Exit boundary

Without explicit authorization for the authenticated check, produce a static
mapping report only and leave provider health unresolved.

## Completion evidence — 2026-08-02

- Configuration maps SiliconFlow to `SILICONFLOW_API_KEY`; the variable was
  present, but its value was never printed or persisted.
- One bounded authorized `GET https://api.siliconflow.cn/v1/models` returned
  HTTP 401. Response body and credential-bearing headers were omitted.
- No credential rotation, endpoint rewrite, completion, paid, or user-pays call
  occurred. SiliconFlow remains unhealthy pending credential/account action.
