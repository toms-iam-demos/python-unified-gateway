---
id: glossary
title: Glossary
owner: you
status: active
last_verified: 2025-12-21
tags: [pug, orientation]
---

# Glossary

## Intent
- Keep terminology consistent across docs, demos, and code.

## Contract
- **Inputs:** Terms used in documentation and code.
- **Outputs:** A single place to define them.
- **Invariants:** Prefer plain language; no vendor-specific jargon unless necessary.

## Terms

**Artifact**
: A file (or folder) written to disk as part of the system’s state. Artifacts are auditable and (usually) immutable.

**Inbox receipt**
: The raw webhook request payload (and headers) saved exactly as received.

**Event (normalized)**
: The canonical representation of a webhook event after normalization, persisted as immutable artifacts.

**Projection**
: A derived, rebuildable view (index, metrics, summaries) computed from immutable events.

**Replay**
: The act of reprocessing previously recorded events to reproduce behavior, test integrations, or run demos.

**ACK-first**
: Webhook endpoints return **200 OK** quickly and never block on downstream processing.

**Idempotency**
: Processing the same inbound event more than once does not create inconsistent state or duplicate side effects.

**Integration adapter**
: A vendor-specific module that verifies payloads, normalizes events, and optionally performs API calls.

**Runbook**
: Step-by-step operational procedure (Day 0 setup, local dev, deploy, incident response).

## References
- Design laws: `20_design-laws.md`
- Event contract: `../02_events/00_event-contract.md`
