---
id: adr-0001
title: External Event Service Is the Authoritative Source of Lifecycle Facts
owner: you
status: accepted
last_verified: 2025-12-21
tags: [adr, events, ingress]
---

# ADR-0001: External Event Service Is the Authoritative Source of Lifecycle Facts

## Intent
Define the authoritative source of lifecycle facts emitted by external systems and establish how those facts enter and persist within the system.

## Status
Accepted

## Context
The system integrates with external platforms that:
- maintain internal lifecycle state machines,
- perform domain-specific operations independently, and
- emit asynchronous notifications describing state transitions.

These notifications may be duplicated, delayed, retried, or delivered out of order.
Alternative interfaces (polling APIs, downstream integrations) do not provide equivalent temporal or evidentiary guarantees.

## Definitions
**External Event Service (Event Feed)**  
A third-party system that owns a lifecycle state machine and emits asynchronous assertions describing state transitions.

Each emitted event represents a claim of the form:

> “For entity X, state transition Y occurred at time T.”

The emitting system is authoritative for the truth of these assertions within its domain.

## Decision
Events emitted by an External Event Service are treated as the authoritative source of lifecycle facts.

Accordingly:
- Lifecycle facts are ingested exclusively from the event feed.
- Events are treated as factual assertions, not commands.
- The gateway deduplicates, orders, and persists events.
- Persisted events form an immutable ledger of external assertions.

Polling interfaces and derived states are not treated as authoritative.

## Rationale
- Event feeds provide definitive temporal assertions.
- Polling introduces ambiguity and race conditions.
- Immutable event ledgers enable replay and audit.

## Consequences
### Positive
- Clear ownership of lifecycle truth
- Deterministic ingestion
- Vendor independence

### Negative
- Requires explicit ordering and deduplication
- Eventual consistency is required

## Alternatives Considered
- Polling APIs (rejected)
- Treating downstream integrations as authoritative (rejected)

## Scope
Applies to all external systems emitting lifecycle events.

## Review Criteria
Revisit if an external system no longer emits lifecycle events.
