---
id: definition-of-done
title: Definition of done
owner: you
status: active
last_verified: 2025-12-21
tags: [pug, quality]
---

# Definition of done

## Intent
- Ensure every feature is shippable, demoable, and auditable.

## Contract
- **Inputs:** A feature / integration / change request.
- **Outputs:** A deliverable that meets operational + review standards.
- **Invariants:** If it can’t be replayed and explained, it’s not done.

## DoD checklist (feature-level)
- [ ] **Docs:** A markdown page exists/updated under `docs/` describing intent + contract + failure modes.
- [ ] **Artifacts:** Any new state is written under `data/` with an immutable artifact layout.
- [ ] **Replay:** A replay scenario exists (selector + expected report output).
- [ ] **Observability:** Logs include correlation identifiers (event_id, run_id).
- [ ] **Safety:** Webhook endpoints remain ACK-first and non-blocking.
- [ ] **Tests:** At minimum, a smoke path for parsing/normalization is covered.
- [ ] **Demo:** Feature is demonstrable offline from recorded events.

## DoD checklist (integration-level)
- [ ] Verification rules (signature/auth) are documented.
- [ ] Normalization mapping is documented.
- [ ] Example payloads are stored as sanitized fixtures (no secrets).
- [ ] Replay scripts cover happy path + at least one failure mode.

## References
- Event contract: `../02_events/00_event-contract.md`
- Live demo checklist: `../07_demo/10_live-demo-checklist.md`
