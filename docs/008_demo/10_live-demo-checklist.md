---
id: live-demo-checklist
title: Live demo checklist
owner: you
status: draft
last_verified: 2025-12-21
tags: [pug, demo]
---

# Live demo checklist (walk-into-a-room)

## Intent
- Provide a repeatable demo flow that works offline from recorded events.

## Contract
- **Inputs:** A set of recorded events + projections, and a replay scenario.
- **Outputs:** A deterministic replay run report and clear narrative.
- **Invariants:** Demos must not depend on real-time vendor availability.
- **Failure modes:** Missing projections; empty event corpus; misconfigured env.

## Pre-demo (5 minutes)
- [ ] `git status` clean (or explain what’s local)
- [ ] `.env` points to demo-safe settings (no production secrets)
- [ ] Confirm `data/` contains recorded events for the narrative
- [ ] Confirm projections exist (or be ready to rebuild)
- [ ] Start API server

## Demo flow (10–15 minutes)

### 1) Orientation (1 min)
- Open `docs/index.md`
- Show “Design laws” and explain: filesystem = state, events immutable, replay mandatory

### 2) Ingest evidence (2–3 min)
- Hit webhook endpoint with a sample payload (or show a prior receipt)
- Show new raw receipt under `data/inbox/...`

### 3) Event artifact (3–5 min)
- Open a normalized event folder under `data/events/.../<event_id>/`
- Highlight:
  - `00_meta.json` (hashes/pointers)
  - `20_norm.json` (canonical event)
  - `30_audit.json` (verification result)

### 4) Replay (3–5 min)
- Trigger replay for a known set of events
- Show `data/replay/runs/<run_id>/report.md`
- Explain how replay is deterministic and auditable

### 5) Close (1–2 min)
- Reiterate: recorded events + docs = repeatable demonstrations, recovery, and audit trail

## Troubleshooting quick hits
- No projections? → run rebuild (admin endpoint or CLI) and continue.
- Signature checks failing? → show `30_audit.json` and explain “recorded evidence + best-effort verification.”
- Vendor API down? → switch to replay-only demo; that’s the point.

## References
- System at a glance: `../00_orientation/00_system-at-a-glance.md`
- Event contract: `../02_events/00_event-contract.md`
- HTTP route map: `../03_api/00_http-api.md`
