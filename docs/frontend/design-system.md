---
title: PUG frontend design specification
version: 1.2.2
status: accepted
owner: PUG project maintainer
updated: 2026-10-09
governing_adr: ADR-0011
---

# PUG frontend design specification

Current specification: September 6, 2026. Governed by [ADR-0011](../007_adr/0011-frontend-architecture-and-design-governance.md).
This document replaces the accumulated historical brand notes retained in the examples project.
Historical instructions about strict docusign color matching, remote-only fonts and
the generated PUG mascot are superseded.

## Platform and profile boundary
This specification describes reusable presentation rules and the generic public-sector presentation contract. PUG is independent of state, sector and organization. Identity assets, colors, terminology, strategy copy and enabled capability mascots are profile-owned choices. Shared components own layout and interaction contracts; profiles must not require organization-specific forks of those components.

The existing hard-coded public-sector implementation has not yet been converted to a configuration-driven profile. Private baseline fidelity and public generic presentation are separate contracts. See the [organization profile contract](organization-profile.md).

## Surface boundaries

The administration console follows the active approved branding profile. The current reference profile combines PUG, docusign-inspired presentation and organization identity. Agency
replicas preserve their own source markup and styles and never inherit the console
base or theme. “Clone” fidelity applies to a named agency reference, not to the
current hybrid console. See the [replica specification](replica-specification.md).

## Generic visual system

| Role | Value | Use |
| --- | --- | --- |
| Navy | #0C1228 | Header and embedded consoles |
| Deep violet | #25104D | Hero transition and developer identity |
| Cobalt | #4C00FF | Secondary links and inherited developer accents |
| Red | #C9233B | Primary actions, selected tabs, emphasis |
| Red hover | #A9162C | Primary-action hover |
| Mist | #CBC2FF | Secondary text on dark surfaces |
| Page gray | #EEEFED | Main canvas |
| Card gray | #F8F9F6 | Light panels and tables |
| Tab gray | #E6E8E5 | Administration navigation |
| Charcoal | #343940 | Light-surface text |
| Muted gray | #626965 | Secondary text on light surfaces |

Use red deliberately, not as the default body-text color. Public demos use neutral original artwork; keep semantic colors consistent.
Keep contrast, focus and keyboard use reviewable; no accessibility certification is claimed.

Typography uses local DSIndigo Regular and Medium files, with Helvetica/Arial fallbacks.
Indigo and developer-center spacing are the design reference, not a claim of current
pixel parity. Source reference sizes include 96px desktop header, 64px developer hero,
48px administration heading and 56px primary actions; responsive/component overrides
are owned by the actual stylesheets. Keep sentences concise and executive copy
focused on services, efficiency and value. Always spell docusign lowercase in authored copy.

## Component ownership

| Component / file | Responsibility |
| --- | --- |
| studio/templates/developer_base.html | Shared document, fonts/styles, header/footer |
| studio/templates/components/developer_header.html | PUG/Python identity and global navigation |
| studio/templates/components/organization_identity.html (proposed generic path) | Generic portfolio identity |
| studio/templates/components/department_identity.html | Normalized department marks and names |
| studio/templates/components/mcp_chat.html | Embedded Sark prompt/results interface |
| studio/static/developer-brand.css | Base semantic tokens and reusable controls |
| studio/static/developer-source.css | Current hybrid refinements and identity styling |
| studio/static/developer-operations.css | Adapter for the existing operations screen |
| studio/static/portfolio.css | Portfolio overview, cards and search presentation |
| studio/static/mcp-chat.css | Embedded console presentation |

New administration pages extend developer_base.html. Existing operations retain their
adapter. The cascade still contains historical overrides; resolve those carefully
when consolidating CSS and verify screenshots before/after. Do not introduce another
independent theme. /brand is the component reference; it must track this specification.

## Public asset standards

Use original neutral artwork for organization types: NFP, Museum, Municipal and EDU. Do not distribute institutional seals, flags, recognizable landmarks, copied wordmarks or source-site screenshots as generic branding. Retain private source evidence separately; publish a separately reviewed derivative.

Preserve aspect ratios, readable labels and keyboard focus. Asset sizing is evaluated against the actual generic artwork, not optical calibration inherited from an identifiable source mark. Retain licenses for distributable third-party fonts and technical product references. Public accessibility and attribution alone do not grant redistribution rights.

The portable examples provide the current generic artwork. Historical studio file paths above identify component responsibilities, not installed packages or an approved source-asset inventory. No private desktop paths or institutional asset filenames belong in the public specification.

## Product and validation rules

The active organization owns homepage identity; the shared public profile uses generic organization types. MCP, CLM and OpenClaw retain dedicated workspaces.
Keep Who / What / How on department examples and provenance/ownership in management
views. The homepage subheading is editorially aligned with
generic public-service outcomes.
Do not imply verified rollout outcomes from configured launches or captured file counts.

The Sark interface is embedded, with sample API commands and no connected model/MCP
transport. Preserve the visible connection disclosure. CLM and OpenClaw are preview
workspaces. Do not substitute visual polish for functionality evidence.

For frontend changes, review component reuse, source-style isolation, responsive
layout, logo proportions, contrast/focus, accurate statuses and relevant behavior.
Use matched screenshots for fidelity claims. Use focused interaction checks for
search and command handling. Live workflow submission is not a visual test.

## Approved branding contract

Use the [organization profile's approved branding contract](organization-profile.md#approved-branding-contract)
for shared tokens, consistent console presentation and recorded approval evidence.
The [governing ADR](../007_adr/0011-frontend-architecture-and-design-governance.md)
continues to define the boundary; this specification does not create another contract.

## Version history

1.0.0  -  September 6, 2026: consolidated visual baseline under ADR-0011.

1.1.0  -  September 6, 2026: distinguish organization-independent platform rules from the public-sector reference profile. No runtime rebranding or multi-tenancy claim.

1.2.0 - September 7, 2026: clarify approved branding, approval evidence and consistent application across console surfaces under ADR-0011.

1.2.1 - September 20, 2026: reference the shared profile contract instead of duplicating it; no branding or architectural change.

## Public identity revision — 2026-10-09

Named organization references have been generalized for distribution. Historical source captures remain private; proposed generic paths are not claims of existing runtime files. Shared demos must use organization types and neutral artwork. No deployed service was rebranded by this documentation revision.

1.2.2 — 2026-10-09: remove residual identifying asset/agency references and separate historical private prototypes from public generic examples.
