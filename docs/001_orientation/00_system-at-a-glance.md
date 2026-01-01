---
id: system-at-a-glance
title: System at a glance
owner: you
status: active
last_verified: 2025-12-21
tags: [pug, orientation, architecture]
---

# System at a glance

## Intent
- Describe PUG in one page that a reviewer can understand in under 60 seconds.
- Establish the “shape” of the system: ingress → artifacts → projections → replay.

## Contract
- **Inputs:** Webhook HTTP requests; operator actions (CLI/UI).
- **Outputs:** Immutable artifacts; rebuildable projections; replay reports.
- **Invariants:** Ingest is fast/ack-first; artifacts are append-only; derived views are disposable.
- **Failure modes:** Disk I/O; verification failure; backlog pressure.

## The big picture

```text
              ┌────────────────────┐
Third-party → │  Webhook Ingest     │  →  200 OK immediately
webhooks       │  (ACK-first)       │
              └─────────┬──────────┘
                        │ write raw receipt (immutable)
                        ▼
                  data/inbox/YYYY/MM/DD/*.json
                        │ normalize asynchronously
                        ▼
              data/events/YYYY/MM/DD/<event_id>/
                00_meta.json
                10_raw.json
                20_norm.json
                30_audit.json
                40_notes.md (optional)
                        │ build derived views (rebuildable)
                        ▼
                 data/projections/latest/*
                        │ replay engine reads immutable events
                        ▼
                 data/replay/runs/<run_id>/*
                   plan.json
                   results.jsonl
                   report.md
```

## Components (runtime)
- **Ingest service (FastAPI):** Receives webhooks and writes raw receipts to `data/inbox/`.
- **Verifier:** Validates signatures/auth context where applicable; records results in audit artifacts.
- **Normalizer:** Converts vendor payloads into a canonical normalized event format.
- **Indexer/Projector:** Creates fast lookup indices and metrics from immutable events.
- **Replay engine:** Replays selected events through integration adapters and produces a report.
- **Docs site + Demo UI:** Read-only surfaces that visualize artifacts and demo runs.

## Key properties (what makes this “enterprise-grade”)
- **Reliability:** Ingest is ACK-first and decoupled from downstream work.
- **Auditability:** Every event becomes an immutable folder with hashes + verification results.
- **Reproducibility:** Demos are replays over recorded events (not live dependencies).
- **Operability:** Runbooks are kept in-repo; derived projections are rebuildable.

## Artifacts
- Event contract: `../02_events/00_event-contract.md`
- HTTP surface: `../03_api/00_http-api.md`
- Local dev: `../05_runbooks/10_local-dev.md`

## References
- ADR template: `../06_adr/0000_template.md`
