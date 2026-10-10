# Repository hygiene and chain of command

Effective 2026-10-09. Owner: repository maintainer.

## Sources of authority

| Question | Authority |
| --- | --- |
| What is authorized? | Maintainer's explicit task scope and approvals |
| What architecture applies? | Accepted ADRs and versioned frontend canon |
| What is published? | Actual GitHub main commit |
| What has been proven? | Test output, CI checks and reviewed PR evidence |
| What is running? | Observed service version and health, independently verified |
| What happened and why? | Versioned change records and PRs; sanitized Notion summaries for discovery |

Agents implement and verify within scope; they do not silently approve their own expansion into deployment, provider-side bulk changes or destructive operations. A factual disagreement between documentation and code must be recorded and resolved, not hidden.

## Folder contract

- `gateway/`: gateway runtime. Changes can affect deployed services and require runtime validation.
- `examples/`: portable, synthetic, reviewed demonstrations with their own setup, dependencies, tests and reset instructions.
- `local-dev/`: ignored working area. `local-dev/pug-examples/` holds candidate demos. Its contents do not transfer through GitHub.
- `docs/007_adr/`: architectural decisions. Reserve numbers across main and outstanding proposals. Proposed decisions are not accepted policy.
- `docs/changes/`: public-safe engineering change records, intentionally distinct from ignored runtime logs.
- Backups: outside the checkout, access-restricted and never published. They can contain secrets and earlier identities.

## Normal work cycle

1. Inspect status, remote, branch and ignored state; fetch origin. Establish the intended baseline. Do not reset over someone else's changes.
2. Create a focused branch. Make one reviewable change and record new assumptions.
3. For an example, verify clean installation, synthetic fixtures, localhost binding, safe reset boundaries and operation without private files. Distinguish simulation from real provider calls in the UI and documentation.
4. Stage explicit files. Inspect staged content, filenames, binary assets and metadata. Check for credentials, identifying data and accidental runtime files. Git ignore rules do not untrack existing files.
5. Run relevant tests, `python tools/check_public_identity.py`, and `git diff --cached --check`. Validate documentation builds when documentation changes. Record commands and outcomes, including checks not run.
6. Push the branch and open a PR. Inspect CI for the actual head commit. Merge only within authorization. Fast-forward local main after merge and confirm it matches origin/main with a clean status.
7. Record final PR/commit/check links in the PR and, if authorized, a sanitized Notion entry. Do not call a local commit pushed, a pushed branch merged, or a merged change deployed.

## Refreshing the entire local checkout

A refresh is maintenance, not a routine substitute for pulling main. Identify running processes and managed worktrees before moving a checkout. Stop or relocate affected processes with appropriate authorization; do not leave them silently attached to the old tree.

Clone main into a temporary sibling first. Confirm clone health and compare its HEAD with the remote. Preserve the old checkout intact outside the repo, including `.git`, ignored and untracked files; use a manifest/hash check when copying rather than renaming. Record the backup path privately. Move the fresh clone into the normal location and verify status and origin. Roll back the rename if replacement fails.

Do not automatically copy `.env`, databases, virtual environments or local experiments back. Restore deliberately when needed. Do not start services or deploy as a side effect. Backup retention/deletion needs a separate maintainer decision; a successful refresh does not authorize deletion.

## Logging contract

For each substantial task record: date, actor, objective, baseline, changed paths, validation evidence, unresolved items and recovery. The [change record template](../changes/TEMPLATE.md) is the minimum format. Keep observed facts separate from plans. Use UTC or explicitly identify the timezone for operational timestamps.

Versioned records explain the change; PRs carry final head/merge evidence. Notion is the human activity index, not a competing copy of architecture or executable configuration. Link to the PR/runbook rather than copying private paths, payloads or credentials. If a Notion write fails or needs approval, say so and retain the repository record; never claim it was logged there.

Runtime logs belong in ignored runtime storage. Use correlation IDs and bounded summaries; avoid tokens, authorization headers and personal document contents. Demo reset and external bulk operations need scope previews, explicit cohort ownership and recorded outcomes.

## Enforcement and limits

The public identity workflow checks known identifiers on pushes and PRs. It does not enforce branch protection, detect all secrets or approve a deployment. Maintainer-configured GitHub rules should prevent force-push/deletion of main and require PR checks; inspect actual settings before claiming those protections exist. This change establishes repository instructions and publication checks, not a new authentication or deployment system.
