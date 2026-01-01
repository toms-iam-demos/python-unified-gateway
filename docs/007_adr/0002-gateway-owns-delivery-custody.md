---
id: adr-0002
title: The Gateway Owns Delivery Custody and Downstream Confirmation
owner: you
status: accepted
last_verified: 2025-12-21
tags: [adr, delivery, custody]
---

# ADR-0002: The Gateway Owns Delivery Custody and Downstream Confirmation

## Intent
Define responsibility for delivering effects to downstream systems and proving acceptance.

## Status
Accepted

## Context
Authoritative events often require downstream actions.
Vendor-managed integrations do not provide sufficient guarantees around retry, confirmation, or replay.

## Decision
The gateway is the sole owner of delivery custody.

Accordingly:
- Delivery intents are created explicitly.
- All downstream actions are executed by the gateway.
- Attempts and outcomes are recorded durably.
- Acceptance must be explicitly confirmed.
- Replay is gateway-controlled.

## Rationale
- Custody requires confirmation and replay
- Centralization prevents silent failure

## Consequences
### Positive
- Deterministic delivery
- Replayable outcomes

### Negative
- Increased gateway responsibility

## Alternatives Considered
- Vendor-managed delivery (rejected)
- Fire-and-forget delivery (rejected)

## Scope
Applies to all downstream effects derived from authoritative events.
