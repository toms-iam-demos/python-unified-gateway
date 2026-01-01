---
id: design-laws
title: Design laws
owner: you
status: active
last_verified: 2025-12-21
tags: [pug, orientation, laws]
---

# Design laws (non-negotiable)

## Intent
- State the rules that keep the system coherent and reviewable.

## Contract
- **Inputs:** Design decisions.
- **Outputs:** Allowed / disallowed patterns.
- **Invariants:** If it violates a law, it doesn’t ship.

## Platform
- macOS (Apple Silicon)
- Python **3.10+**
- Explicit virtual env (`venv` or `pyenv`)
- Docker **CLI only** via **Colima**
- **No Docker Desktop**

## Architecture
- **Filesystem = state**
- **Markdown = documentation truth**
- **Events are immutable**
- Webhooks return **200 OK immediately**
- **Replayability is mandatory**

## Professional standard
If a design decision cannot be explained to a state IT architect in under **60 seconds**, it does not belong here.

## Implementation guardrails
- Prefer small modules with clear boundaries.
- Never couple webhook ACK latency to downstream work.
- Write raw receipts first; normalize later.
- Derived views must be rebuildable from immutable artifacts.
- Secrets never enter artifacts; store only references/hints.

## References
- System overview: `00_system-at-a-glance.md`
- ADRs: `../06_adr/0000_template.md`
