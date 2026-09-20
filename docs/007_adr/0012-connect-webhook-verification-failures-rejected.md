---
id: adr-0012
title: Connect Webhook Verification Failures Are Rejected, Not Quarantined
owner: PUG project maintainer
status: accepted
last_verified: 2026-09-20
tags: [adr, security, ingress, docusign]
---

# ADR-0012: Connect Webhook Verification Failures Are Rejected, Not Quarantined

## Intent
Record the failure-handling policy for docusign Connect verification and the
tradeoff against ADR-0010's auditability requirement.

## Status
Accepted. The September 20 clarification below preserves the reject-before-persistence
policy; it corrects its scope and describes the accompanying explorer accurately.

## Context
[ADR-0010](0010-external-event-feed-authentication-and-integrity.md) requires source
authentication and integrity verification before deduplication or persistence.
It permits rejection or quarantine of failed events. For this ingress, PUG chooses
rejection before the authoritative ledger write path.

## Decision
`POST /webhooks/docusign` verifies HMAC-SHA256 over the original request bytes,
using one configured receiver key and all numbered docusign signature headers.
Any matching signature is sufficient, supporting provider key rotation.

- Missing, malformed or nonmatching signatures return HTTP 401.
- An absent or blank `DOCUSIGN_CONNECT_HMAC_SECRET` returns HTTP 503.
- Rejected requests are neither parsed into the event envelope, persisted nor broadcast.
- Accepted requests reach the existing ledger path with `verify_status=verified`
  and `verify_reason=hmac-sha256`.

This is the rejection option in ADR-0010. It does not create a quarantine store.

## Rationale
Rejecting before persistence prevents unverifiable requests from writing rows through
this ingress into the authoritative ledger. A quarantine in the same ledger would
allow unauthenticated callers to reach that write path, even if rows were flagged.
A separate quarantine store would require its own retention, access and capacity design.

Failing closed on missing configuration prevents an unnoticed downgrade to unverified
ingestion. Provider retries may recover transient verification failures, but operators
must confirm the actual Connect retry behavior and delivery backlog during rollout;
this policy does not guarantee eventual delivery.

## Consequences and limits
New rows admitted through this route have passed a shared-secret integrity check.
That establishes possession of the configured key, not independent proof of a human
sender's identity or a fresh event. Signed payloads may be replayed; existing deduplication
still governs repeated bodies. Existing unverified ledger rows are not retroactively
validated. Other write paths, if added, need their own verified admission boundary.

Persistence remains best-effort: a verified request can return HTTP 200 with
`persisted=false`. Verification does not imply durable custody. A duplicate insert is
ignored; it does not upgrade an older row's verification metadata. The persistence
helper can also report a newly generated event ID that does not resolve to the existing
duplicate row. These pre-existing ledger semantics are outside this decision.

A rejected legitimate request has no ledger body to inspect or replay. Recovery depends
on provider redelivery or another authorized recovery source. Rejections are logged by
`gateway.connect_hmac`: WARNING for invalid/missing signatures, ERROR for missing
configuration. These lines include reasons, not secrets, signatures or payloads.

When the opt-in explorer is enabled, completed rejected requests also appear as bounded,
process-local status and failed-span metadata. This is volatile evidence, not a durable
rejection audit log, and it contains no rejected body. Log retention and operational
monitoring remain necessary to satisfy the observable/auditable failure intent of
ADR-0010. `/health` does not test the HMAC key or successful ledger persistence.

## Alternatives considered
- Quarantine in the authoritative ledger: not selected because it opens a ledger write
  path to unverified traffic and requires operators to distinguish flagged records.
- Fail open when no key is configured: rejected because it silently removes the trust boundary.
- Separate quarantine storage: a possible future design, not implemented here.

## Scope and review criteria
This decision applies to `POST /webhooks/docusign`. Other feeds must record their own
failure-handling policy. Review it if provider retries, recovery requirements or durable
rejection observability change. Adding rejection counters alone does not require changing
the rejection policy; changing the admission/quarantine boundary requires a superseding ADR.

## Review history
- **2026-09-19:** recorded the existing reject-before-persistence policy.
- **2026-09-20:** clarified shared-key trust, historical/duplicate rows, log levels,
  optional explorer visibility and the remaining durability gap. No policy change.

## Links
- [HMAC runbook](../006_runbooks/12_connect_hmac.md)
- [Explorer runbook](../006_runbooks/13_architecture_explorer.md)
- Implementation: `gateway/connect_hmac.py`, `gateway/routers/webhooks.py`
- Tests: `tests/test_connect_hmac.py`
