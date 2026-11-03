# Reconcile deployed gateway source

Date: 2026-11-02 (America/Los_Angeles)

The maintainer requested repository catch-up and release preparation. Merged the existing operator-audit branch, including its Workflow Builder and full API ancestors, into current main without replacing newer website, publication hygiene or generic example work. Resolved the documentation navigation conflict by retaining repository hygiene and adding the three gateway runbooks.

The API remains sandbox-bound, operator-authenticated and read-only: six reviewed reads, with the other 418 documented operations locked before credentials or provider calls. Workflow discovery is separately gated. Operator audit records contain bounded metadata and block execution or withhold results on recording failure. This is source reconciliation of already-deployed behavior, not new provider permissions or a service rollout.

Added the missing pytest test-runner dependency and a gateway CI workflow that runs all test styles together, the identity guard and an image build. Fixed a strict documentation-build link to the website README. Tests, documentation, publication review and CI outcomes are recorded in the PR. Existing connected demo services and their private state were not changed. Previous stacked PRs become superseded only when this merge reaches main.

Rollback: revert the integration merge for source. No running-service rollback is needed because traffic and containers were not replaced.
