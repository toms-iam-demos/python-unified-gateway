---
title: Frontend product specification
version: 1.1.0
status: accepted
owner: PUG project maintainer
updated: 2026-09-06
governing_adr: ADR-0011
---

# Frontend product specification

## Organization-independent product model
The default entry is the active organization's portfolio, with units and use cases described using its terminology. A unit may be a department, division, business line, campus or other grouping. Discovery, management, operator workspaces and evidence views are reusable capabilities. Enable workspaces through profile configuration; no organization must adopt every integration.

Arkansas remains the current reference deployment. The routes below describe implemented behavior, not a required public URL vocabulary for every organization. A future generic routing layer must preserve existing links or document migration. A single configured instance does not establish secure multi-tenancy.

## Current Arkansas navigation contract

| Route | Purpose and current state |
| --- | --- |
| / and /admin/departments | Arkansas-led portfolio, overview counts, searchable department examples |
| /admin/departments/{id} | Owner/notes, provenance and next steps |
| /examples | Developer example gallery |
| /studio | Simulated agreement, draft and delivery operations |
| /admin/mcp | Embedded Sark command console; model/MCP not connected |
| /admin/clm | Dedicated lifecycle preview |
| /admin/openclaw | Dedicated agent-workspace preview |
| /brand | Inspectable design components |

## Reusable interaction contract
Each unit/use-case card presents Who / What / How and opens its replica. Search supports matching, no-results feedback and reset by clearing input. The homepage remains the portfolio when capabilities are added.

MCP interaction stays inline; no pop-outs. Sark's caption is “end of line.” Current commands read sample APIs, show expandable results and explicit errors, and support clearing the transcript. Keep the model/connection disclosure visible. CLM scope belongs in its own workspace rather than repeated exclusion text.

DF&A's configured Maestro launch occurs only through the explicit launch action. Launch counts are not completion metrics. Do not present captures, configured examples or sample records as verified organization-wide deployment progress.

## Outstanding acceptance work
Matched responsive screenshots, complete keyboard review, durable browser interaction tests and registry-derived overview counts remain follow-up work. Live integrations need separately specified behavior and access controls.

## Version history

1.0.0 — September 6, 2026: establishes the accepted baseline from the frontend work; governed by ADR-0011. Future revisions record rationale and validation evidence.

1.1.0 — September 6, 2026: distinguish organization-independent platform rules from the Arkansas reference profile. No runtime rebranding or multi-tenancy claim.
