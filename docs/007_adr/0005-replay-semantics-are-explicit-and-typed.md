---
id: adr-0005
title: Replay Semantics Are Explicit and Typed
owner: you
status: accepted
last_verified: 2025-12-21
tags: [adr, replay]
---

# ADR-0005: Replay Semantics Are Explicit and Typed

## Intent
Prevent ambiguity in historical reprocessing.

## Status
Accepted

## Context
Failures and policy changes require replay.

## Decision
Replay is explicitly defined as:
1. Transform replay
2. Delivery replay
3. Full re-ingest

These are not interchangeable.

## Rationale
- Prevents duplication
- Preserves audit integrity

## Scope
Applies to all historical correction workflows.
