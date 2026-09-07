---
title: PUG frontend design specification
version: 1.1.0
status: accepted
owner: PUG project maintainer
updated: 2026-09-06
governing_adr: ADR-0011
---

# PUG frontend design specification

Current specification: September 6, 2026. Governed by [ADR-0011](../007_adr/0011-frontend-architecture-and-design-governance.md).
This document replaces the accumulated historical brand notes retained in the examples project.
Historical instructions about strict docusign color matching, remote-only fonts and
the generated PUG mascot are superseded.

## Platform and profile boundary
This specification describes reusable presentation rules and the current Arkansas reference profile. PUG is independent of state, sector and organization. Identity assets, colors, terminology, strategy copy and enabled capability mascots are profile-owned choices. Shared components own layout and interaction contracts; profiles must not require organization-specific forks of those components.

The existing hard-coded Arkansas implementation has not yet been converted to a configuration-driven profile. Keep its accepted appearance while extracting that boundary in follow-up implementation. See the [organization profile contract](organization-profile.md).

## Surface boundaries

The administration console is the approved PUG/docusign/Arkansas hybrid. Agency
replicas preserve their own source markup and styles and never inherit the console
base or theme. “Clone” fidelity applies to a named agency reference, not to the
current hybrid console. See the [replica specification](replica-specification.md).

## Arkansas reference profile: visual system

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

Use red deliberately, not as the default body-text color. Preserve original flag
and department-mark colors; grayscale treatment applies to surrounding surfaces.
Keep contrast, focus and keyboard use reviewable; no accessibility certification is claimed.

Typography uses local DSIndigo Regular and Medium files, with Helvetica/Arial fallbacks.
Indigo and developer-center spacing are the design reference, not a claim of current
pixel parity. Source reference sizes include 96px desktop header, 64px developer hero,
48px administration heading and 56px primary actions; responsive/component overrides
are owned by the actual stylesheets. Keep sentences concise and leadership copy
focused on services, efficiency and value. Always spell docusign lowercase in authored copy.

## Component ownership

| Component / file | Responsibility |
| --- | --- |
| studio/templates/developer_base.html | Shared document, fonts/styles, header/footer |
| studio/templates/components/developer_header.html | PUG/Python identity and global navigation |
| studio/templates/components/arkansas_identity.html | Official flag and portfolio identity |
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

## Arkansas reference profile: asset standards

| Identity | Current asset | Presentation |
| --- | --- | --- |
| PUG | studio/static/pug-logo.png | User-supplied pixel mark; 64px desktop / 56px mobile; lighten blend on isolated navy header |
| Python | studio/static/python-purple.png | Supplied purple mark in shared technology badge |
| MCP / Sark | studio/static/sark-mcp.png | MCP tab/console; caption “end of line” |
| OpenClaw / Larry | studio/static/larry-openclaw.png | OpenClaw tab/page on white plate; supplied checkerboard remains in original asset |
| Arkansas | studio/static/state/arkansas-flag.jpg | Complete original flag, native proportions and colors |
| DF&A | studio/static/departments/dfa-supplied.jpg | Latest supplied green seal; multiply blend on pale-gray holder |
| Military | studio/static/departments/military.png | Official source mark |
| Veterans Affairs | studio/static/departments/veterans.png | Official source mark |
| ADH | studio/static/departments/health.svg | Official source mark and optical-size reference |
| Agriculture | studio/static/departments/agriculture.png | Official source mark |

Department holders are 92px desktop / 72px mobile, with a 1px border and 5px padding.
Target visible emblem diameters are 80px / 60px. Compensate source margins with CSS
scales: DF&A 1.057, Military 1.333, Veterans 1.0508, ADH 1.0, Agriculture 1.1062.
Use containment and preserve aspect ratio. Source files remain unchanged; inspect
optical alignment after any replacement instead of assuming equal canvases imply equal marks.

Department source URLs and hashes are in
asset provenance (`pug-examples/studio/static/departments/sources.json`; external working example). PUG, Python and Sark
were supplied from Desktop/Dev; Larry from the same folder; DF&A from Desktop/df&a.jpg.
Do not reuse the older generated pug-mark-v1.png or superseded DF&A seals in new UI.

Flag source: [Arkansas Secretary of State](https://www.sos.arkansas.gov/education/arkansas-history/history-of-the-flag/),
[original image](https://ee-sos-site.ark.org/uploads/education/AR_Flag.jpg), retrieved September 6, 2026.
Font source: [developer-center font stylesheet](https://developers.docusign.com/fonts/dist/css/OliveFonts.css).
Publicly accessible assets and user-supplied artwork require redistribution review
before public publishing; source attribution alone does not grant a license.

## Product and validation rules

The active organization owns homepage identity; Arkansas is the current profile. MCP, CLM and OpenClaw retain dedicated workspaces.
Keep Who / What / How on department examples and provenance/ownership in management
views. The homepage subheading is editorially aligned with
[Arkansas Forward](https://governor.arkansas.gov/wp-content/uploads/AR-Forward.pdf).
Do not imply verified rollout outcomes from configured launches or captured file counts.

The Sark interface is embedded, with sample API commands and no connected model/MCP
transport. Preserve the visible connection disclosure. CLM and OpenClaw are preview
workspaces. Do not substitute visual polish for functionality evidence.

For frontend changes, review component reuse, source-style isolation, responsive
layout, logo proportions, contrast/focus, accurate statuses and relevant behavior.
Use matched screenshots for fidelity claims. Use focused interaction checks for
search and command handling. Live workflow submission is not a visual test.

## Version history

1.0.0 — September 6, 2026: consolidated visual baseline under ADR-0011.

1.1.0 — September 6, 2026: distinguish organization-independent platform rules from the Arkansas reference profile. No runtime rebranding or multi-tenancy claim.
