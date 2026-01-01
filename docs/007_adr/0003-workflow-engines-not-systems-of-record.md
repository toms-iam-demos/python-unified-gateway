---
id: adr-0003
title: Workflow Engines Are Not Systems of Record
owner: you
status: accepted
last_verified: 2025-12-21
tags: [adr, workflow]
---

# ADR-0003: Workflow Engines Are Not Systems of Record

## Intent
Separate execution flow from authoritative state custody.

## Status
Accepted

## Context
Workflow engines coordinate steps and waits but maintain mutable, execution-scoped state.

## Decision
Workflow engines are not authoritative systems of record.

Authoritative facts must be persisted independently of workflow execution.

## Rationale
- Workflow state is transient
- Custody must survive reconfiguration and replay

## Consequences
- Clear execution/truth separation
- Stable audit records

## Alternatives Considered
- Treating workflows as authoritative (rejected)

## Scope
Applies to all workflow orchestration tools.
