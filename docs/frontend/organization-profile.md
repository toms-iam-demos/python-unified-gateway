---
title: Organization profile contract
version: 1.0.0
status: accepted-design
owner: PUG project maintainer
updated: 2026-09-06
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

## Version history
1.0.0 — September 6, 2026: accepted organization-independent design contract; implementation pending.
