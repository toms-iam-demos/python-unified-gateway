# Fixed degraded database detail in readiness responses

On November 9, 2026, the gateway changed `GET /health/ready` to return
`database unavailable` as `db.detail` when SQLite reports degraded mode.
The HTTP status, JSON shape, readiness flags, and healthy and disabled
responses retain their existing behavior. The route still calls the same
schema check, and internal diagnostics and `GET /health` are unchanged.

## Verification

- The focused test verifies all three database modes, the absence of a
  synthetic private error detail, and liveness without a schema check.
- The isolated AMD64 gateway suite passed 69 tests and 12 subtests, with
  one existing Starlette TestClient deprecation warning.
- Both Traefik 3.6.16 HTTP and browser checks passed on the Linux AMD64
  candidate
  `sha256:6d69646806fe6ae7b55674a678124df0686b90156a33f2c9cd17467f675c1488`.
  They used synthetic credentials and signed deliveries, isolated HTTP,
  and temporary SQLite. They verified operator access, HMAC receipt
  persistence, deduplication, and truncated preview masking.

## Recovery

The change is limited to response formatting. It requires no schema,
configuration, or data changes. The candidate was verified locally.

## Production cutover and live acceptance

On November 9, 2026, at 6:12:12 p.m. Pacific, the gateway started on
Linux AMD64 image
`sha256:6ab70d0b0b0b845406fb9a6c80672ba74991424a3e83f20281d612cac4266f69`,
built from `79f9f4a80847a9f395e88b3c3ae1239b214aae16`. Both SQLite backup
checksums and isolated restore checks passed. Only the gateway was recreated,
with orphan removal disabled. The rollback image `51e5edb6c02c` remained
available, and rollback was unnecessary.

Loopback and public HTTPS health passed. Production readiness reported
`ready: true` and `db.mode: "ok"`. The operator confirmed that the monitor
and event browser worked in the signed-in production session.

At 6:13:37 p.m. Pacific, an organic Docusign delivery returned HTTP 200.
The monitor confirmed persistence and matched HMAC-verified SQLite ledger
receipt `bdce16d2-e054-4aad-a054-c7eda22a7fc4`. No webhook was triggered for
verification. Live cutover acceptance passed.
