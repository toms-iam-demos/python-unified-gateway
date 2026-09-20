# Python Unified Gateway

**A lightweight, Python-native integration layer for enterprise systems.**

Organizations run on systems that were never designed to work together. Python Unified Gateway (PUG) provides a common boundary for connecting their APIs, events and workflows.

Built to run locally and deploy as a containerized service, PUG keeps integration logic explicit, inspectable and adaptable as platforms change.

## What’s here

- **Python and FastAPI** for a programmable service layer.
- **Verified event ingestion** and a persistent SQLite ledger.
- **Event inspection** through APIs and a browser monitor.
- **Optional request tracing** and architecture exploration.
- **Documented decisions and tested behavior** alongside the code.

docusign is the first implemented connection. The architecture is intended for integrations across business, government and other complex organizations.

## Direction

Consistent event contracts, downstream adapters, reliable delivery and controlled replay.

PUG is under active development. See the [runbooks](docs/006_runbooks/10_local-dev.md) for setup and operational limits, and the [architecture decisions](docs/007_adr/index.md) for the thinking behind it.

**Small enough to understand. Built to connect.**
