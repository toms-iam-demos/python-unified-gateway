# Working in PUG

These instructions apply to this repository and its agents and contributors.

## Authority and truth

- The maintainer sets scope, approves consequential operations, and resolves conflicts. Never infer permission to deploy, send messages, perform bulk writes/deletes, or rewrite history from a code change.
- GitHub `main` is the published source of truth. A checkout, backup, prototype, chat or Notion entry is not evidence of what is published or deployed.
- Follow accepted ADRs in `docs/007_adr/` and the frontend canon in `docs/frontend/`. If a requested change conflicts, identify the conflict and record the maintainer's decision; do not silently supersede policy.
- Evidence wins over assumptions: distinguish proposed, implemented, locally tested, CI passed, merged and deployed.

## Working rules

1. Inspect branch, remote, status and applicable instructions before changing anything. Fetch before deciding what main contains. Do not overwrite concurrent changes.
2. Work on a focused branch. Stage named files and inspect the staged diff, including assets and generated outputs. No blanket staging of experiments.
3. Keep unproven work in ignored `local-dev/`; group demo experiments in `local-dev/pug-examples/`. Promote only a reviewed, portable subset into `examples/`.
4. Never commit credentials, customer records, runtime databases, private screenshots or institution-specific branding. Follow the public identity policy, including ADRs and generated assets.
5. Run relevant tests and the publication identity check against all staged additions. Passing the identity check does not prove secrets are absent; inspect the diff separately.
6. Use a pull request, inspect checks and changes, then merge within maintainer authorization. Never force-push main. A merge is not a deployment.
7. Record substantial work in `docs/changes/` with scope, evidence, limitations and recovery. Use the PR for final merge/check evidence. Mirror a sanitized summary to Notion only when authorized and available; report if it was not saved.
8. Before replacing a checkout, preserve all tracked, untracked, ignored and Git state outside it. Verify the backup and refresh from the intended remote. Never restore private state automatically. Backup deletion is a separate action.

See `docs/006_runbooks/15_repository-hygiene.md` for the operating procedure.
