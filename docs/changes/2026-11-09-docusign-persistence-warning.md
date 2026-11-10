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

## Production cutover and live acceptance

On November 9, 2026, at 5:25:39 p.m. Pacific, the gateway started on
Linux AMD64 image
`sha256:51e5edb6c02cb38a8133263ae05faa712547298560f68f097da0432ab40089bb`
built from `f338f0997095273be828a1dde7029f397bd5ac95`. Refreshed SQLite
backup checksums and isolated restore checks passed. Only the gateway
was recreated, with orphan removal disabled. The other project container
inventory was unchanged. The prior image `5dbbcf738ea4` remained available
for rollback. No rollback was needed, and 3.051 GB remained free.

Loopback and public HTTPS health passed. Mounts, network, and port binding
matched the baseline. The monitor and event browser pages, assets, and
feeds responded, and unauthenticated public requests to protected routes
returned HTTP 401. The operator separately confirmed the monitor and
event browser in the signed-in production browser session.

At 5:30:39 p.m. Pacific, an organic Docusign delivery returned HTTP 200.
The monitor reported successful persistence and its event ID matched
HMAC-verified SQLite ledger receipt `32853a9b-9d5f-460b-8c58-30b5bd99fa80`.
No webhook was triggered for verification. Live cutover acceptance passed.
