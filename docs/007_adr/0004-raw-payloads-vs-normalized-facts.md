---
id: adr-0004
title: Raw External Payloads Are Retained Short-Term; Normalized Facts Are Retained Long-Term
owner: you
status: accepted
last_verified: 2025-12-21
tags: [adr, data]
---

# ADR-0004: Raw External Payloads Are Retained Short-Term; Normalized Facts Are Retained Long-Term

## Intent
Define retention strategy for externally sourced event data.

## Status
Accepted

## Context
Raw payloads are large, vendor-specific, and unbounded in growth.

## Decision
Raw payloads are retained for a bounded window.
Normalized canonical facts are retained indefinitely.

## Rationale
- Normalized facts preserve long-term value
- Raw payloads create unbounded growth

## Consequences
- Controlled storage growth
- Reduced vendor coupling

## Alternatives Considered
- Retaining raw payloads indefinitely (rejected)

## Scope
Applies to all externally sourced event payloads.
