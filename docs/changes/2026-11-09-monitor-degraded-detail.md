# Fixed degraded persistence detail in webhook monitor events

On November 9, 2026, the gateway began using `database unavailable` for
`persistence.db_detail` when a verified Docusign webhook reports degraded
persistence. The handler formats a copy when assembling the event shared by
the monitor feed and stream broadcaster. The original result and internal
diagnostics are unchanged.

The existing fail-open HTTP 200 response with `persisted: false` and the
monitor's `warn` status are preserved. Disabled-mode detail, successful
receipts, duplicate identifiers, and signature rejection retain their
existing behavior.

## Verification

- The focused regression checked degraded and disabled responses, the
  event in the monitor feed, the event passed to the broadcaster, and
  preservation of the original persistence result.
- The isolated Linux AMD64 gateway suite passed 70 tests and 14 subtests,
  with one existing Starlette TestClient deprecation warning.
- Both Traefik 3.6.16 HTTP and browser checks passed on candidate
  `sha256:0b08db0a2e5c1427bdceadfc7585e99491a07faeb35a1c8e6eadb114d652a73c`.
  They used synthetic credentials and signed deliveries with temporary
  SQLite. They covered operator authentication, matching ledger receipts,
  deduplication, and truncated preview masking. The browser used polling.
  Stream coverage was limited to the event passed to the broadcaster.

## Recovery

The change only formats the monitor event. Reverting it requires no
schema, configuration, or data changes.

## Production cutover and live acceptance

On November 9, 2026, at 6:38:41 p.m. Pacific, the gateway started on
Linux AMD64 image
`sha256:c069e53c97cfceec9cd80be079acd92c3e80698418d43afcb8bdbf47b76ed884`
built from `5b6634711e1da2b911477711757233a6795f2432`. Both SQLite backup
checksums and isolated restore checks passed. Only the gateway was recreated,
with orphan removal disabled. Rollback image `6ab70d0b0b0b` remained
available, and rollback was unnecessary.

Loopback and public HTTPS health passed, and readiness reported a healthy
database. The operator confirmed the monitor and event browser worked in
the signed-in production session.

At 6:40:05 p.m. Pacific, an organic Docusign delivery returned HTTP 200.
The monitor confirmed persistence, and its event ID matched HMAC-verified
SQLite receipt `abe22cf6-a4cd-4468-b5e2-b7ad598c59a5`. No webhook was
triggered for verification. Live cutover acceptance passed.
