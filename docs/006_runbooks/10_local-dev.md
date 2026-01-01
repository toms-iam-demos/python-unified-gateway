---
id: local-dev
title: Local development runbook
owner: you
status: draft
last_verified: 2025-12-21
tags: [pug, runbook, local]
---

# Local development runbook

## Intent
- Get a dev instance running locally with artifact storage and a minimal demo loop.

## Contract
- **Inputs:** A macOS machine, Python 3.10+, project checkout.
- **Outputs:** Running API server; artifacts written to `data/`; docs site runnable.
- **Invariants:** No Docker Desktop; local-first; state is filesystem.
- **Failure modes:** Python env drift; missing deps; disk permissions.

## Prereqs
- Python 3.10+
- `venv` or `pyenv`
- (Optional) Colima + Docker CLI if you use containers for ancillary services

## One-time setup

```bash
cd python-unified-gateway

python3 -m venv .venv
source .venv/bin/activate

pip install -U pip
pip install -e ".[dev]" || pip install -r requirements.txt
```

Create local environment file:

```bash
cp .env.example .env
# edit .env with your local values
```

Initialize local state directories:

```bash
mkdir -p data/inbox data/events data/projections data/replay data/logs
```

## Run the API (dev)

```bash
# example
uvicorn pug.app:app --reload --host 127.0.0.1 --port 8080
```

## Quick smoke: simulate a webhook

```bash
curl -X POST "http://127.0.0.1:8080/webhooks/example" \
  -H "Content-Type: application/json" \
  -d '{"hello":"world"}'
```

Expected:
- HTTP 200 quickly
- New files appear under `data/inbox/...`

## Run docs locally (MkDocs)

```bash
pip install mkdocs-material
mkdocs serve
```

Open the local docs URL printed by mkdocs.

## Artifacts
- Inbox receipts: `data/inbox/YYYY/MM/DD/*.json`
- Normalized events: `data/events/YYYY/MM/DD/<event_id>/`
- Projections: `data/projections/latest/*`
- Replay runs: `data/replay/runs/<run_id>/*`

## References
- Design laws: `../00_orientation/20_design-laws.md`
- HTTP route map: `../03_api/00_http-api.md`
