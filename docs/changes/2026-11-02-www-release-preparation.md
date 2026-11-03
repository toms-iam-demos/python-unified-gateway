# Website release preparation

Date: 2026-11-02 (America/Los_Angeles)

The maintainer requested that the existing repository catch up with website development and that a release be prepared for Hetzner, while the agreement-agent acceptance checks run separately. This is preparation, not permission to replace active services before their checks finish.

## Source consolidation

Updated the existing website branch and PR, retaining the schema-v2 taxonomy work, registered example identities and isolated presentation bridge. Restored the original geometric home hero at `/`. Home and the product link use `/`; the obsolete catalog overview redirects there. App Center is a catalog-owned collection, with the observed 104 non-Microsoft apps/templates. Stripe is enabled only by a hosted deployment profile; other entries remain disabled placeholders. Provider icons remain profile-owned assets. Added a plain, single-example invitation draft flow. It sends no email and grants no access.

The public bundled catalog contains generic examples and no provider connection. Approved organization branding, production links, recorded sessions and legacy organization aliases belong in the private deployment profile. Provider command execution remains disabled in the migration presentation bridge. This package must not silently replace the existing working connected runtimes.

The Dockerfile copies only package source and dependency manifests. Local environments, build outputs, databases, Finder sidecars and private profiles are excluded. Changed and untracked files were preserved outside the repository before cleanup. Unrelated work and historical backups were not deleted.

## Validation

Fifteen tests passed against the installed Python 3.12 package, covering authenticated routes, fail-closed configuration, root routing, App Center placeholder counts and Stripe profile activation, invitation draft boundaries, canonical example aliases, preserved presentation styling, and locked provider commands. JavaScript syntax passed. Browser checked the home hero, a one-example Stripe invitation draft, all 104 App Center entries and a Zendesk search returning one entry. Publication scan and final GitHub checks are recorded in the PR.

## Deployment boundary

The running site is still split across the catalog/classification service and the visitor service. The visitor service owns `/` and enforces scoped guest access. The new standalone package does not implement that guest session boundary. Existing agent, classification, rules, Stripe, CLM, HAM and clickthrough services retain their own state and routes. A broad replacement of `/catalog` would also capture legacy query-area pages, so it is not an acceptable shortcut.

The prepared release archive contains committed website source only. It is suitable for an isolated candidate image, not an automatic ingress cutover. Before activation: finish agent checks, preserve all current catalog entries and links in a validated deployment profile, retain the visitor root boundary, reconcile legacy area routing, and verify all connected targets. Use ready-before-switch traffic changes and retain old image digests and route configuration for rollback. Do not run Compose over unrelated services.

Older deployed gateway changes remain on the existing stacked PRs. Their merge state must not be confused with the website PR or with server health. No claim that every running service is reproducible from main is made by this preparation record.
