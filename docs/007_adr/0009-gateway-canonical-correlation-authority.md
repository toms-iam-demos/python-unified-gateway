---
id: adr-0009
title: The Gateway Is the Canonical Correlation Authority
owner: you
status: accepted
last_verified: 2025-12-21
tags: [adr, correlation]
---

# ADR-0009: The Gateway Is the Canonical Correlation Authority

## Intent
Establish authoritative cross-system correlation.

## Status
Accepted

## Decision
The gateway assigns and owns correlation identifiers linking events, state transitions, deliveries, and outcomes.
External identifiers are treated as inputs, not narrative authority.

## Rationale
- Enables traceability
- Prevents vendor lock-in

## Scope
Applies to all persisted records.
