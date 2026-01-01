---
id: index
title: python-unified-gateway
owner: you
status: active
last_verified: 2025-12-21
tags: [pug, overview]
---

# python-unified-gateway (PUG)

**Local-first API orchestration, webhook ingestion, and demonstration platform**

---

## Intent

The python-unified-gateway exists to:

- Provide a production-grade webhook spine that reliably ingests third-party events.
- Normalize events into immutable artifacts that can be replayed deterministically.
- Demonstrate and exercise external APIs repeatably (live + offline).
- Treat documentation, logs, and artifacts as first-class outputs.

This is not a throwaway demo framework. It is intended to behave like a system a real team could own.

---

## Contract

- **Inputs:**  
  Third-party webhooks; operator CLI commands; demo scripts.

- **Outputs:**  
  Immutable event artifacts; reproducible replay runs; documentation and runbooks; observable logs.

- **Invariants:**
  - Filesystem = state
  - Markdown = documentation truth
  - Events are immutable
  - Webhook endpoints return **200 OK immediately**
  - Replayability is mandatory

- **Failure modes:**  
  Disk unavailable/full; invalid signatures; malformed payloads; dependency outages; operator error.

These invariants are not aspirational. They are enforced by design.

---

## Documentation model (how to read this repository)

This documentation is intentionally **layered**.  
Not all documents serve the same purpose, and not all are equally mutable.

### 1. Genesis — how constraints were earned

→ **`000_genesis/`**

- A time-ordered development record.
- Captures decisions, missteps, reversals, and constraints as they were discovered.
- Preserved as historical record.
- **Not canonical** and should not be edited for clarity or tone.

This is where the system’s constraints were *earned*, not declared.

---

### 2. Orientation — how the system should be understood today

→ **`001_orientation/`**

- Canonical mental models.
- Design laws.
- Definitions of done.
- Invariants that must not be broken.

This is the first authoritative layer for readers who want to understand the system as it exists now.

---

### 3. Architecture and contracts — what exists and how it fits together

→ **`002_architecture/`**  
→ **`003_events/`**

- Structural decomposition.
- Data flow.
- Event contracts and schemas.

These sections describe the system’s shape, not its history.

---

### 4. Interfaces — how to interact with the system

→ **`004_api/`**

- HTTP endpoints.
- Integration surfaces.
- Request/response expectations.

---

### 5. Operations — what to do under time pressure

→ **`006_runbooks/`**

- Step-by-step operational procedures.
- Written for operators.
- Assumes the system already exists and is running.

Runbooks optimize for action, not explanation.

---

### 6. Decisions — why certain choices are locked in

→ **`007_adr/`**

- Architecture Decision Records.
- Append-only once accepted.
- Linked back to Genesis steps where the decision emerged.

---

### 7. Demonstrations

→ **`008_demo/`**

- Live demo checklists.
- End-to-end walkthroughs.
- Example flows meant to be exercised, not merely read.

---

## Reading guidance

- Do **not** treat Genesis as a tutorial.
- Do **not** edit historical phase files for clarity.
- Refinements, reinterpretations, and future direction belong in:
  - Orientation documents
  - ADRs
  - Explicit addenda (when necessary)

This structure exists to prevent context loss, accidental regression, and the slow erosion of system intent.
