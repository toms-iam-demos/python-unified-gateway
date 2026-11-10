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
