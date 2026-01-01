---
id: adr-0007
title: Authoritative Decisions Require Live Authoritative Systems
owner: you
status: accepted
last_verified: 2025-12-21
tags: [adr, decisions]
---

# ADR-0007: Authoritative Decisions Require Live Authoritative Systems

## Intent
Define where outcome-affecting decisions originate.

## Status
Accepted

## Decision
Authoritative decisions must be based on live authoritative systems.
Cached data may be used only for non-decisional enrichment.

## Rationale
- Prevents staleness
- Ensures defensibility

## Scope
Applies to all outcome-affecting logic.
