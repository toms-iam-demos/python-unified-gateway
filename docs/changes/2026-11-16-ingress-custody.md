# Change record: Connect ingress custody hardening

- Date / timezone: 2026-11-16, America/Los_Angeles.
- Actor and authorization: coding agent, on the maintainer's explicit instruction to fix four reviewed ingress findings on a new branch off main.
- Baseline commit: `56978eb` (main, PR 38).
- Objective and scope: `POST /webhooks/docusign` only. `gateway/routers/webhooks.py`, `gateway/db/events_store.py`, tests, ADR-0012 consequences/review history, runbooks 12 and 13.
- Changed behavior:
  1. A verified event that is not persisted returns 503 with `Retry-After: 60` (was 200, `persisted=false`), so Connect redelivers it. An explicitly disabled ledger (`GATEWAY_DB_ENABLED=0`) still answers 200. The monitor still shows the event as `warn`.
  2. Deduplication ignores the top-level `retryCount` field, which Connect increments on redelivery. Payloads without that field keep their existing raw-body key. The first delivery's original bytes are stored.
  3. `correlation_id` is always server-generated (ADR-0009). Client `X-Correlation-Id`/`X-Request-Id` values remain in `headers_json` as unverified input.
  4. Bodies over `DOCUSIGN_CONNECT_MAX_BODY_BYTES` (default 16 MiB; invalid or non-positive values use the default) return 413 before HMAC verification, whether declared by `Content-Length` or found by the streaming read. They are not persisted or broadcast.
- Validation: `python -B -m pytest -q tests` passed 86 tests (20 subtests) under the maintained Python 3.12.12 environment. The six new tests failed against the baseline gateway code and pass with the fix. `tests/acceptance/rehearse.cjs` now asserts a server-generated correlation UUID; it was not run in this change. `python tools/check_public_identity.py` passed.
- Not tested / limitations: No live Connect delivery was exercised. Redelivery after 503 depends on the account's Connect retry configuration ("require acknowledgement"), which was not inspected. Connect's `retryCount` placement follows the documented JSON payload and was not compared with stored production rows. Events stored before this change have raw-body keys, so the first redelivery of such an event after deployment adds one row. If Connect is configured to include documents, confirm the 16 MiB default is enough before deploying. Producers whose bodies differ only by top-level `retryCount` are now treated as duplicates.
- Recovery and backup location: revert the PR's commits. No schema migration or data change; no backup required.
- PR / release reference: pending. No deployment.
- Notion mirror status: not requested.
