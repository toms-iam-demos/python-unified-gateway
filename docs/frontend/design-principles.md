---
title: Frontend design principles
version: 1.2.1
status: accepted
owner: PUG project maintainer
updated: 2026-09-20
governing_adr: ADR-0011
---

# Frontend design principles

## Audience and intent
PUG serves organizational leaders overseeing agreement operations, people participating in business/service journeys, and practitioners inspecting implementation evidence. This can be any organization or sector; public-service language is not mandatory platform copy.

The reusable identity combines developer-oriented clarity with an approved organization brand. Typography, spacing, accessible interactions and shared components provide coherence; organization profiles supply identity assets, palette choices, terminology and outcome messaging. The current docusign-inspired/Arkansas blend is the first reference profile, not a required state identity for all deployments.

Source-based replicas follow the originating organization's reference, even when its styling differs from the console. Preserve source identity, document intentional adaptations and avoid unsupported claims of ownership or deployed results. Keep implementation details where they help the audience make decisions. Write docusign lowercase when referring to that integration.

Keep visible logo sizes consistent within each profile; ADH is the optical reference for the current Arkansas profile only. Capability mascots and captions are profile presentation choices, not architectural dependencies. The user-approved current Arkansas deployment retains its existing appearance.

## Arkansas reference profile
Arkansas Forward informs that profile's public-service, efficiency and taxpayer-value language. Other profiles use their own approved strategy and audience vocabulary. No organization's strategy should be baked into the reusable shell.

## References
- [Current design specification](design-system.md)
- [Arkansas Forward](https://governor.arkansas.gov/wp-content/uploads/AR-Forward.pdf)
- [Governing ADR](../007_adr/0011-frontend-architecture-and-design-governance.md)

## Approved branding contract

Use the [organization profile's approved branding contract](organization-profile.md#approved-branding-contract)
for shared tokens, consistent console presentation and recorded approval evidence.
The [governing ADR](../007_adr/0011-frontend-architecture-and-design-governance.md)
continues to define the boundary; this specification does not create another contract.

## Version history

1.0.0  -  September 6, 2026: establishes the accepted baseline from the frontend work; governed by ADR-0011. Future revisions record rationale and validation evidence.

1.1.0  -  September 6, 2026: distinguish organization-independent platform rules from the Arkansas reference profile. No runtime rebranding or multi-tenancy claim.

1.2.0 - September 7, 2026: clarify approved branding, approval evidence and consistent application across console surfaces under ADR-0011.

1.2.1 - September 20, 2026: reference the shared profile contract instead of duplicating it; no branding or architectural change.
