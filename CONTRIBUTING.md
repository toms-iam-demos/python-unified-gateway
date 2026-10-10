# Contributing to PUG

Read [repository instructions](AGENTS.md) and the [working procedure](docs/006_runbooks/15_repository-hygiene.md) first.

Use a focused branch and pull request. Keep drafts in ignored `local-dev/`; publish self-contained examples in `examples/`. The maintainer owns scope and release decisions. GitHub main records the published source, while deployment status must be verified independently.

Before publication, stage only intended paths, inspect `git diff --cached`, run relevant tests and `python tools/check_public_identity.py`, and verify setup from a clean checkout. Record substantial work under `docs/changes/`. Do not put secrets, real personal data or private operational details in commits, PRs or logs.

An architectural change needs an ADR using the shared sequence. Check both main and outstanding proposals before assigning a number. Routine housekeeping uses the runbook and change record rather than a new ADR.
