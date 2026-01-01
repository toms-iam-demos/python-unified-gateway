---
id: http-api
title: HTTP API surface
owner: you
status: draft
last_verified: 2025-12-21
tags: [pug, api, fastapi]
---

# HTTP API surface (route map)

## Intent
- Provide a single authoritative list of HTTP endpoints exposed by PUG.
- Describe the contract and filesystem effects for each endpoint.
- Make ACK-first behavior explicit for webhook ingress.

## Contract
- **Inputs:** HTTP requests.
- **Outputs:** ACK responses; artifact writes; read-only views.
- **Invariants:** Webhooks ACK fast; writes are append-only; derived views rebuildable.
- **Failure modes:** Disk unavailable; invalid request shape; auth failures for admin endpoints.

> This is a **documentation map** of routes (not an OpenAPI dump, not a redesign).

---

## Ingress (webhooks)

### POST `/webhooks/{provider}`
**Purpose**
- Ingest third‑party webhooks (ACK-first).

**Behavior**
- Writes raw receipt to `data/inbox/…` (immutable).
- Records verification outcome (best-effort).
- Schedules normalization asynchronously.
- Returns **200 OK immediately**.

**Filesystem effects**
- **Writes:** `data/inbox/YYYY/MM/DD/*.json`, `*.headers.json`
- **Does not write synchronously:** `data/events/*`, `data/projections/*`

**Failure modes**
- Disk unavailable → `503`
- Malformed request → still `200` (receipt saved + audit marks parse failure), unless payload cannot be written

---

## Read-only (docs + artifacts)

### GET `/health`
**Purpose**
- Liveness/readiness indicator.

**Behavior**
- Returns minimal JSON: status, time, version.

**Filesystem effects**
- None.

### GET `/artifacts/events`
**Purpose**
- Browse/search events (powered by projections).

**Behavior**
- Reads projections/index; never mutates state.

**Filesystem effects**
- **Reads:** `data/projections/latest/*`

> If projections missing, endpoint may return `404` or trigger rebuild (choose one and document it).

---

## Admin (optional, protect behind auth)

### POST `/admin/projections/rebuild`
**Purpose**
- Rebuild projections from immutable events.

**Behavior**
- Triggers rebuild job.

**Filesystem effects**
- **Writes:** `data/projections/latest/*` (rebuildable)

### POST `/admin/replay`
**Purpose**
- Start a replay run from a selector + plan.

**Filesystem effects**
- **Writes:** `data/replay/runs/<run_id>/*`

---

## Notes for maintainers
- Every route added must be documented here with:
  - purpose
  - sync guarantees
  - filesystem effects
  - failure modes

## References
- Event contract: `../02_events/00_event-contract.md`
- Local dev: `../05_runbooks/10_local-dev.md`
