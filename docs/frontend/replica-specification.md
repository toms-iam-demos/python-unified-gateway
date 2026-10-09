---
title: Source replica specification
version: 1.1.1
status: accepted
owner: PUG project maintainer
updated: 2026-10-09
governing_adr: ADR-0011
---

# Source replica specification

## Scope
Applies to any organization's authorized source-based demonstration: public agency, business, university or other institution. Public availability is not assumed for all sources. Access and asset reuse must be authorized; do not capture private material merely because a browser session can reach it.

Public distribution uses generic organization types and separately sanitized derivatives. Identifying source captures, captured forms and configuration bindings remain outside the public package. A generic derivative must not be described as an exact replica of an unnamed real organization.

## Required record for each private source example
Record source authorization, capture time, asset hashes, baseline viewport, intentional changes and review results in the private source register. Preserve baseline bytes. Never publish private source URLs, real workflow bindings or identifying artwork merely to prove provenance. If an asset license requires identifying attribution, retain the credit only in an authorized distribution or replace the asset; do not strip required attribution.

## Shared example contract
The public catalog describes the scenario, synthetic fixture version, generic identity, implemented capabilities and tested limitations. NFP, Museum and Municipal are runnable examples; EDU is reserved for future scenarios. Public examples do not imply access to a real organization's staff systems.

## Acceptance criteria
Compare source and replica at matching desktop/mobile sizes; verify content and navigation; inspect forms and launch behavior without unintended submission; check keyboard focus and legibility. Record every approved deviation. A captured page with scripts/forms suppressed is a preview until these differences are reviewed. Source updates require a new baseline and comparison, not silent overwrite.

Keep capture integrity, visual status, behavior status and integration status distinct. Current source snapshots cover HTML and directly linked CSS; some assets remain remote. No blanket exact-clone or offline-completeness claim is approved.

## Variant handling
An improved use-case version preserves its baseline reference and records which changes are intentional, who approved them and how they were verified. Version source and improved variants independently; do not overwrite evidence to make a modified page appear to be the original.

## Version history

1.0.0 — September 6, 2026: establishes the accepted baseline from the frontend work; governed by ADR-0011. Future revisions record rationale and validation evidence.

1.1.0 — September 6, 2026: distinguish organization-independent platform rules from the public-sector reference profile. No runtime rebranding or multi-tenancy claim.

## Public identity revision — 2026-10-09

Named organization references have been generalized for distribution. Historical source captures remain private; proposed generic paths are not claims of existing runtime files. Shared demos must use organization types and neutral artwork. No deployed service was rebranded by this documentation revision.

1.1.1 — 2026-10-09: remove residual identifying asset/agency references and separate historical private prototypes from public generic examples.
