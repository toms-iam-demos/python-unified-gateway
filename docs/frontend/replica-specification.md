---
title: Source replica specification
version: 1.1.0
status: accepted
owner: PUG project maintainer
updated: 2026-09-06
governing_adr: ADR-0011
---

# Source replica specification

## Scope
Applies to any organization's authorized source-based demonstration: public agency, business, university or other institution. Public availability is not assumed for all sources. Access and asset reuse must be authorized; do not capture private material merely because a browser session can reach it.

The Arkansas examples below are the current reference catalog, not the platform schema. Replica fidelity remains tied to its source organization independently of the active console profile.

## Required record for each example
The department registry and timestamped capture manifests identify source URLs, capture times, asset files and hashes. Maintain a separate working template and record its intentional differences from the source. Add the source/replica viewport pair, visual review date, reviewer, behavioral checks and result before promoting its status to validated.

| Example | Current baseline and adaptation |
| --- | --- |
| DF&A vehicle POA | Motor Vehicle Forms source page; POA entry adapted to explicit configured Maestro redirect |
| Military | Captured state timesheet/leave notice; current form and workflow await owner validation |
| Veterans Affairs | Captured rules/application entry; 2026 Child Welfare application is the research reference |
| Health / ADH | Captured food-protection/plan-review entry; workflow configuration pending |
| Agriculture | Captured pesticide-registration entry; preserve distinct mail and online channels |

Source details: department registry (`pug-examples/studio/departments.json`; external working example). Working HTML: replicas (`pug-examples/studio/templates/replicas/`; external working example) and DF&A entry (`pug-examples/studio/templates/motor-source.html`; external working example).

## Acceptance criteria
Compare source and replica at matching desktop/mobile sizes; verify content and navigation; inspect forms and launch behavior without unintended submission; check keyboard focus and legibility. Record every approved deviation. A captured page with scripts/forms suppressed is a preview until these differences are reviewed. Source updates require a new baseline and comparison, not silent overwrite.

Keep capture integrity, visual status, behavior status and integration status distinct. Current source snapshots cover HTML and directly linked CSS; some assets remain remote. No blanket exact-clone or offline-completeness claim is approved.

## Variant handling
An improved use-case version preserves its baseline reference and records which changes are intentional, who approved them and how they were verified. Version source and improved variants independently; do not overwrite evidence to make a modified page appear to be the original.

## Version history

1.0.0 — September 6, 2026: establishes the accepted baseline from the frontend work; governed by ADR-0011. Future revisions record rationale and validation evidence.

1.1.0 — September 6, 2026: distinguish organization-independent platform rules from the Arkansas reference profile. No runtime rebranding or multi-tenancy claim.
