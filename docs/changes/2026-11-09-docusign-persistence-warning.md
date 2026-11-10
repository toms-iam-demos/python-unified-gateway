# Docusign webhook persistence warning

On November 9, 2026, the gateway added a fixed-text warning when a
signature-verified Docusign webhook fails to produce a persisted receipt.
The warning contains no payload, headers, identifiers, database details,
or exception text. Fail-open behavior is unchanged. The response remains
HTTP 200 with `persisted: false`, and the monitor still marks the event
`warn`. Signature rejection and successful persistence behavior are unchanged.

## Verification

- The focused regression asserted exactly one fixed-text warning on
  simulated ledger failure, the existing HTTP response and monitor
  behavior, and no warning for invalid signatures or successful writes.
- The isolated Linux AMD64 Python suite passed 68 tests and 9 subtests.
  It emitted one existing Starlette TestClient deprecation warning.
- Both Traefik 3.6.16 acceptance modes passed on the local AMD64 candidate
  image `sha256:142666707d7cd091c0e3ef096c5ef54bb2b0abaf41d3ae7e05016dc07a948a0c`.
  The tests used synthetic credentials and deliveries, temporary SQLite,
  and isolated HTTP routing. They covered authentication, receipt matching,
  deduplication, browser rendering, and masking. Production routing, TLS,
  and SSE were outside the rehearsal scope.

## Recovery

Reverting this change removes the warning. No schema or configuration
changes are involved. The candidate was verified locally.
