# Restore illustrated workups across demo examples

Date: 2026-11-03.

The detailed workflow narrative is restored inside the existing demo workup, including ordered steps, decision branches, descriptions and evidence labels. All current catalog examples now have a tailored workup that distinguishes recorded implementation from design and retained specifications.

The new shared renderer provides workflow illustrations, evidence, system boundaries and acceptance gates. Its coverage validator rejects missing or incomplete example workups. Eight component tests passed, and desktop and phone layouts were inspected. The illustration headings remain in the document flow to avoid overlapping navigation or static text.

This public change contains the reusable component and its contract. Institution-specific presentation content and private evidence remain outside this repository. The renderer performs no provider operations and does not change access permissions.
