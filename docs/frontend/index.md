# Frontend documentation

## Governing decision

[ADR-0011: Frontend Design Architecture and Governance](../007_adr/0011-frontend-architecture-and-design-governance.md) is the single active architecture decision for this frontend. It is registered in the normal PUG ADR sequence.

## Current specifications

| Artifact | Version | Responsibility |
| --- | --- | --- |
| [Design principles](design-principles.md) | 1.1.0 | Audience, hybrid identity and tone |
| [Product specification](product-specification.md) | 1.1.0 | Navigation, journeys and capability states |
| [Design system specification](design-system.md) | 1.1.0 | Typography, colors, logos and components |
| [Replica specification](replica-specification.md) | 1.1.0 | Source fidelity, deviations and acceptance |
| [Organization profile contract](organization-profile.md) | 1.0.0 | Configuration boundary; implementation pending |

All specifications follow ADR-0011. Changes record version, owner, date, rationale and evidence. No lower-level version may override architecture. Archive the previous specification when publishing a replacement; this table always identifies the current version.

The platform is organization-independent. Arkansas is the current reference profile, not a prerequisite. Current specification revisions preserve the preserved 1.0.0 baseline in the examples project documentation history.

## Canonical ownership

This directory is the authoritative specification source after this review is merged.
The standalone examples app is not included in this documentation change. Its source,
assets and local validation evidence remain a separate working implementation; paths
below identify those artifacts and are not published-site links. Distribution copies
must identify a source commit and content checksum rather than becoming competing
editable authorities.

## Evidence and history

- Source and workflow registry (`pug-examples/studio/departments.json`; external working example)
- Department logo provenance (`pug-examples/studio/static/departments/sources.json`; external working example)
- Workflow tests (`pug-examples/tests/test_workflows.py`; external working example)
- Development checkpoint (`pug-examples/docs/checkpoint-2026-09-06.md`; external working history)
- Superseded ADR-FE history (`pug-examples/docs/adr/index.md`; external working history)

Selected screenshots and ad hoc interaction checks exist from development. A complete approved visual baseline and accessibility audit are still outstanding; documentation acceptance does not imply validation completion.
