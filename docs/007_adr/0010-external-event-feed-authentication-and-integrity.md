---
id: adr-0010
title: External Event Feed Authentication and Integrity
owner: you
status: accepted
last_verified: 2025-12-21
tags: [adr, security, ingress]
---

# ADR-0010: External Event Feed Authentication and Integrity

## Intent
Define the trust boundary for admitting external lifecycle events into the authoritative event ledger.

## Status
Accepted

## Context
Events are treated as authoritative lifecycle facts (ADR-0001).
Because they arrive over untrusted networks, their source and integrity must be verified before persistence.

## Decision
Events are admitted to the authoritative ledger only if:
- the event source is authenticated, and
- payload integrity is verified.

Events failing verification are rejected or quarantined and do not influence system state.

Verification occurs before deduplication, ordering, or persistence.

## Rationale
- Unauthenticated events are meaningless
- Trust must be enforced at ingress
- Silent corruption is unacceptable

## Scope
Applies to all authoritative external event feeds.

## Operational Invariants
- Authentication supports rotation
- Integrity checks are deterministic
- Failures are observable and auditable

## Alternatives Considered
- Network trust alone (rejected)
- Downstream verification (rejected)

## Review Criteria
Revisit if authentication mechanisms materially change.
