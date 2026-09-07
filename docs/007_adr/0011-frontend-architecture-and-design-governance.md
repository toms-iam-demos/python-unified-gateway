---
id: adr-0011
title: Frontend Design Architecture and Governance
owner: PUG project maintainer
status: accepted
decision_date: 2026-09-06
last_verified: 2026-09-06
tags: [pug, adr, frontend, design, governance]
---

# ADR-0011: Frontend Design Architecture and Governance

## Intent
Make PUG recognizable as a product, adaptable to any organization, and faithful to the experiences it demonstrates. Establish the architectural boundaries that let design evolve without fragmenting the platform or misrepresenting its capabilities.

## Status
Accepted as design direction on September 6, 2026. Repository review and merge establish its release baseline; acceptance does not imply that every requirement is implemented or verified.

This record consolidates and supersedes the initial ADR-FE-0001–0004 records. It belongs to the normal PUG ADR register. The earlier records remain historical material, not separate active authorities.

## Context
The first reference implementation combines an administration portfolio, organizational source-page replicas and operator workspaces. Its console evolved into an approved blend of docusign developer typography, PUG identity and Arkansas branding. That work exposed two distinct needs: a consistent product experience and accurate demonstrations of another organization's experience.

Arkansas demonstrates the design; it does not define the platform. The same architecture must accommodate a business, university, nonprofit, government or other organization without duplicating the shared frontend. Design intent needs a durable home, while colors, components, journeys and source examples need room to evolve.

## Decision
Adopt one organization-independent frontend architecture with three explicit design boundaries, governed by this ADR and implemented through versioned specifications.

### 1. Product shell: shared structure and behavior
The PUG shell owns reusable layout, navigation patterns, accessible interaction, component contracts and the presentation of operational evidence. Administration pages compose shared components rather than create independent themes or organization-specific template forks.

The shell must distinguish what is simulated, configured, connected, executed and verified. A polished interface cannot establish authority or execution. Browser actions use explicit application/gateway interfaces; credentials remain server-side. Existing PUG decisions continue to govern event authority, correlation, enrichment context, delivery custody and replay semantics.

FastAPI, Jinja and vanilla JavaScript are the current implementation. This ADR requires the boundaries and contracts, not permanent allegiance to those technologies.

### 2. Organization profile: identity and business context
A versioned profile supplies an organization's identity, approved brand assets and semantic theme tokens, terminology, outcome messaging, use-case catalog and enabled workspaces. It references server-side integration configuration without containing credentials.

Shared components consume that configuration. Changing organizations must not require changing their source to replace names, seals, strategy language or organizational hierarchy. “Department” is one configurable unit label; the reusable concepts are organization, unit, use case and capability workspace.

The approved docusign-inspired/Arkansas visual blend is the first reference profile. Its colors, logo treatments, mascot captions and public-service language belong in its specifications, not in universal platform rules. Organization customization must preserve component behavior, accessibility requirements and truthful state presentation.

Profile selection is not authorization. Supporting multiple profiles does not establish tenant authentication or data isolation. Concurrent multi-organization hosting requires an explicit security and deployment design.

### 3. Source replica: independent fidelity contract
A replica belongs to its identified source experience. It must not inherit the administration theme merely because the console links to it. Preserve captured source material separately from editable working replicas.

Use “clone” only with a defined fidelity target: source URL or authorized reference, capture date, relevant viewport, expected behavior and documented deviations. Validate visual fidelity and functional behavior separately. A complete capture is not a validated clone; a launched workflow is not a completed agreement.

An improved demonstration remains traceable to its baseline. Record intentional changes and their approval rather than silently redefining the source. Source brands establish context, not ownership or endorsement of PUG. Record provenance and review asset reuse before distribution.

## Documentation contract
One architecture decision governs a small set of purpose-specific artifacts:

| Artifact | Owns | Changes when |
| --- | --- | --- |
| This ADR | Architectural boundaries and governing rules | A boundary or invariant changes |
| Design principles | Audience, identity intent, tone and experience goals | Approved design intent evolves |
| Product specification | Journeys, navigation and capability states | Product behavior changes |
| Design system specification and components | Tokens, typography, assets, layouts and interaction standards | Presentation or reusable implementation changes |
| Organization profile and replica contracts | Organization configuration, source baselines and approved adaptations | An organization or example is introduced or revised |
| Validation evidence | Observed conformance to identified versions | A relevant implementation or baseline changes |
| Change history | Rationale, approval and supersession | A reviewed change is accepted |

The documentation index identifies one current version of each specification. Specifications must conform to this ADR; components implement their applicable specifications; tests and reference screenshots establish conformance. Design and product specifications are complementary—neither may silently override the other. Resolve conflicts in a reviewed specification change.

Historical notes, development checkpoints and example copies cannot override current specifications. Keep implementation status separate from design intent so a requirement is never mistaken for a delivered capability.

## Change control
- **Routine evolution:** update the affected specification, components and relevant evidence together. Record version, status, owner, date and rationale. Use a major version for incompatible intent or contract changes, a minor version for compatible additions and a patch for corrections. A version increment does not permit an architectural exception.
- **Architectural change:** create a normal-numbered superseding ADR when changing these boundaries. Use dated clarifications for corrections that preserve the decision; do not rewrite accepted rationale without a record.
- **Accountability:** the PUG maintainer approves product/design intent. Implementation review checks contracts and behavior; design review checks presentation and accessibility. The responsible source/workflow owner approves replica adaptations where applicable. One person may perform multiple roles; the review still records the responsibilities and evidence.
- **Exceptions:** document scope, owner, reason and review date. A temporary specification exception cannot bypass an architectural invariant or justify an unsupported fidelity, security or execution claim.

## Consequences
The architecture allows organizations to share a coherent platform without sharing a visual identity. It also permits accurate source demonstrations without contaminating the administration design system.

The cost is explicit configuration and evidence management. Profiles, components, source captures and specifications can drift; versioned references and focused review are required. Some replicas may retain external asset dependencies, and source changes can invalidate prior verification.

A single stylesheet for every surface would be simpler but would destroy source fidelity. A frontend fork per organization would accommodate customization but multiply maintenance and inconsistent behavior. Recording every visual choice as an ADR would preserve history at the expense of a usable architecture register. These alternatives are rejected.

## Acceptance and current position
The architecture's defining extension check is a second, non-government organization configured without modifying the shared shell. Verify that its identity, terminology, catalog and enabled workspaces change correctly, and that reference-profile names or assets do not leak into it.

Frontend changes must also demonstrate the relevant interaction behavior, source-style isolation and accurate capability states. Appearance changes require review at declared desktop/mobile viewports. Accessibility and clone-parity claims require corresponding evidence. Document-only changes require consistency and link checks, not an application rebuild.

The current Arkansas implementation is a reference baseline, not full conformance: profile configuration has not been extracted from hard-coded templates/routes. A complete visual regression baseline, accessibility audit, validated replica parity and live AI/MCP integration remain outstanding. These are tracked implementation and validation gaps, not exceptions to this decision.

## Related decisions and canonical location
[ADR-0002](0002-gateway-owns-delivery-custody.md) and
[ADR-0003](0003-workflow-engines-not-systems-of-record.md) govern delivery custody and
workflow-engine authority; [ADR-0005](0005-replay-semantics-are-explicit-and-typed.md)
governs replay. ADR-0006–0009 govern gateway access, authoritative decisions, authoring
boundaries and correlation. This record does not alter those contracts.

The canonical ADR is `docs/007_adr/0011-frontend-architecture-and-design-governance.md` in the PUG repository. The examples project carries a synchronized distribution copy of this same record.

The [frontend documentation index](../frontend/index.md) identifies the canonical
specifications in this repository. Example packages may carry generated distribution
copies identifying the source commit and content checksum. They must not be maintained
as independent authorities.

## Review history
- **2026-09-06:** consolidated the initial frontend decisions into the normal ADR register.
- **2026-09-06:** clarified organization independence; Arkansas is a reference profile.
- **2026-09-06:** editorial/design review organized the accepted intent around product shell, organization profile and source replica, and clarified acceptance versus implementation evidence. Previous text retained in the examples documentation history; no invariant was relaxed.

- **Release review:** supporting specifications consolidated into the core documentation tree; distribution copies require source revision and checksum. No runtime release is implied.
