# Fresh checkout and repository working agreement

- Date: 2026-10-09 (America/Los_Angeles).
- Actor: Codex, on the maintainer's request to refresh local main and establish working and logging practices.
- Baseline: `58755e93c276a991a0cc6c61351e5fc4ac102b18` from GitHub main.
- Refresh: cloned main before replacement; confirmed the prior working tree had no tracked changes; preserved the entire prior checkout by rename outside the repository. The earlier full development backup remains retained. Confirmed the fresh clone's baseline before starting this branch.
- Scope: root agent/contributor instructions, a repository runbook, public-safe change record template, PR checklist and explicit ignore boundaries for local experiments and documentation build output.
- Validation: publication identity scan returned zero failures; all five identity regression tests passed; strict MkDocs build passed with pinned documentation dependencies; staged whitespace check passed; ignore probes confirmed local experiments and site output are excluded. See the PR for CI and final publication state. No application behavior was changed.
- Recovery: the previous checkout remains intact in private backup storage. A normal revert can undo the published documentation/ignore change. Backups are not deleted by this task.
- Limits: no production deployment, provider API operation, history rewrite or GitHub branch-rule change. Private experiments and secrets were not restored automatically. No new architecture decision number was allocated; outstanding proposals must be reconciled before numbering.
- Notion mirror: not saved as part of this repository record; a separate successful Notion write is required before reporting one.
