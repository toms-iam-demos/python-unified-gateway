# Architecture Decision Records (ADRs)

This section documents the key architectural decisions that govern the system.

Each ADR captures:
- the context of the decision,
- the decision itself,
- the rationale and tradeoffs,
- and the consequences over time.

## Index

- [ADR-0001: External Event Service Is the Authoritative Source of Lifecycle Facts](0001-external-event-service-authoritative-ingress.md)
- [ADR-0002: The Gateway Owns Delivery Custody and Downstream Confirmation](0002-gateway-owns-delivery-custody.md)
- [ADR-0003: Workflow Engines Are Not Systems of Record](0003-workflow-engines-not-systems-of-record.md)
- [ADR-0004: Raw External Payloads Are Retained Short-Term; Normalized Facts Are Retained Long-Term](0004-raw-payloads-vs-normalized-facts.md)
- [ADR-0005: Replay Semantics Are Explicit and Typed](0005-replay-semantics-are-explicit-and-typed.md)
- [ADR-0006: Documentation Is Static-First; Live Data Access Requires Gateway APIs](0006-static-first-docs-live-data-via-gateway.md)
- [ADR-0007: Authoritative Decisions Require Live Authoritative Systems](0007-authoritative-decisions-require-live-systems.md)
- [ADR-0008: Pro Notebooks Are Authoring Tools; Published Artifacts Are Static or Browser-Safe](0008-pro-notebooks-are-authoring-only.md)
- [ADR-0009: The Gateway Is the Canonical Correlation Authority](0009-gateway-canonical-correlation-authority.md)
- [ADR-0010: External Event Feed Authentication and Integrity](0010-external-event-feed-authentication-and-integrity.md)
