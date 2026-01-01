---
id: data-flow
title: Data flow
owner: you
status: draft
last_verified: 2025-12-21
tags: [pug, architecture, dataflow]
---

# Data flow

## Intent
- Describe how data moves through PUG from inbound webhook to replay report.
- Make coupling points explicit (HTTP → filesystem → projection → replay).

## Contract
- **Inputs:** Webhook HTTP request; operator replay request.
- **Outputs:** Immutable event artifacts; rebuildable projections; replay run outputs.
- **Invariants:** ACK-first; immutable events; rebuildable projections.
- **Failure modes:** Disk I/O; queue/backlog; malformed payloads; external API outages.

## Flow: ingest → normalize → project → replay

1) **Receive webhook**
- Endpoint accepts request and immediately prepares an ACK response.
- The request is *not* trusted; it is treated as evidence.

2) **Persist raw receipt (immutable)**
- Save payload + headers into `data/inbox/YYYY/MM/DD/…`
- Compute and record hashes.

3) **Verify (best-effort, recorded)**
- Signature verification is attempted (provider-specific).
- Result is recorded in audit artifacts (success/fail/unknown).

4) **Normalize into canonical event**
- Provider payload → canonical `20_norm.json`.
- Normalizer must be deterministic given the same receipt.

5) **Build projections (optional, rebuildable)**
- Indices for fast browsing and dashboards.
- Metrics snapshots.

6) **Replay**
- Replay engine selects events (by date/provider/type/run plan).
- Produces:
  - `plan.json`
  - `results.jsonl`
  - `report.md`

## Coupling points (keep these tight)
- **HTTP surface → inbox:** should be minimal and stable.
- **Inbox → normalized events:** deterministic transform with versioning.
- **Events → projections:** pure functions; projections can be deleted/rebuilt.
- **Events → replay:** replay only reads immutable events; it never mutates them.

## Artifacts
- Event contract: `../02_events/00_event-contract.md`
- HTTP routes: `../03_api/00_http-api.md`

## References
- ADR template: `../06_adr/0000_template.md`
