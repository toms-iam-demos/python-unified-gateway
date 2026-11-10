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
