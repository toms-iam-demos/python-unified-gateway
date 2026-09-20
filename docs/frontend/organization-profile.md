---
title: Organization profile contract
version: 1.1.0
status: accepted-design
owner: PUG project maintainer
updated: 2026-09-07
governing_adr: ADR-0011
---

# Organization profile contract

This is the intended configuration boundary. A profile loader, generic routing and profile validation are not implemented yet.

| Profile concern | Required intent |
| --- | --- |
| Identity | Stable organization ID, profile version, display name and approved identity assets |
| Brand | Semantic theme tokens, typography choices and asset provenance; shared component layout stays reusable |
| Terminology | Organization-unit labels and audience vocabulary without assumptions about government |
| Messaging | Approved outcome copy tied to the organization's strategy |
| Catalog | Units, use cases, Who / What / How, owners and explicit readiness states |
| Source replicas | Source organization/page, dated baseline, capture manifest and intentional adaptations |
| Capabilities | Enabled workspace IDs and presentation metadata; integration status is independent of visibility |
| Workflow bindings | References to server-side integration configuration, never credentials or secret launch URLs |
| Evidence | Profile version, capture/test version and validation status used for a demonstration |

## Extension acceptance criteria
Configure a second non-government organization without editing shared shell templates. Verify that names, badges, strategy copy, unit labels and source references do not leak between profiles. Disabled workspaces must disappear from navigation without implying authorization enforcement. Validate required fields, missing assets and unsupported capabilities with clear errors.

Keep profile selection and data authorization distinct. Supporting multiple profile files in separate local instances is not secure concurrent multi-tenancy. Runtime isolation and access controls need a separate design if shared hosting is requested.

## Approved branding contract

All console surfaces consume the same approved, versioned organization profile through shared components and semantic tokens. This includes the homepage, capability tabs, Insights and administrative views. Typography, colors, identity assets, logo sizing, terminology and messaging must remain consistent. Per-page brand variants require a recorded, scoped exception.

Record the brand owner or authorized delegate, approval date, profile version, applicable surfaces and asset provenance. PUG product approval and organization brand approval are distinct. Source replicas follow their own approved fidelity baselines, preserving their visual identity independently of the console.

## Version history
1.0.0  -  September 6, 2026: accepted organization-independent design contract; implementation pending.

1.1.0 - September 7, 2026: clarify approved branding, approval evidence and consistent application across console surfaces under ADR-0011.
