# Verification — 7 October 2026

Scope: standalone local procurement simulation. Reviewed publication branch: `examples/museum-procurement-demo`.

- Fresh temporary venv, macOS arm64, Python 3.14.3; requirements installed successfully.
- `python -m pytest -q`: **7 passed**. Covers local token/origin/host boundaries, invalid sizes/quantities, approval required, reference-only action, duplicate suppression, exact acceptance arithmetic, durable unknown-outcome recovery with a fresh client, version conflict/replan, cohort reset preserving foreign records, 10,000-record seed and complete export.
- Browser: loaded loopback site, seeded three records, selected equipment service, prepared $54,500 target, approved demo plan, executed with lost response, observed unknown, reconciled to verified. PO version advanced once and value remained $54,500. Zero provider calls.
- Runtime database and virtual environments are ignored. Sources contain no credentials, real personal records, customer documents, remote trigger URLs or copied brand assets. Architecture sources use fictional IDs and amounts.
- Publication review: production Docker allowlist excludes `examples/`. New CI workflow only installs dependencies and runs tests; it has read-only repository permissions and no deployment step.

Limits: Windows and Linux runtime tests have not yet been run locally. CI is configured for Python 3.11 on Linux, but its result is not claimed here. Dependency deprecation warnings occur under Python 3.14. No penetration test, full dependency audit, real identity separation, docusign connection, OIC adapter or Oracle tenant verification is claimed. Tests model the destination within one SQLite transaction; a real distributed integration requires independent contract, concurrency and recovery tests.
