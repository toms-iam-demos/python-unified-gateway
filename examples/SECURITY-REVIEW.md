# Portable example collection review — 2026-10-07

## Scope and result

Reviewed the portable NFP expense, Museum procurement and Municipal procurement packages together. This is a targeted code and dependency review, not a penetration test or certification. They run independently with Python virtual environments; no package imports the deployed gateway, calls a provider, sends mail, or initiates payments.

## Changes and evidence

- Consolidated the expense package with the procurement examples on one branch; no need to combine branches on a work machine.
- Updated all three runtimes to FastAPI 0.142.4 and Uvicorn 0.54.0. A pip-audit scan of these requirements and resolved dependencies reported no known vulnerabilities at review time. Direct pins are not a complete transitive lock; repeat the audit when installing or upgrading.
- Bounded POST/PUT/PATCH request bodies to 128 KiB before parsing. Tests exercise oversized bodies and multiple chunks with a misleading Content-Length. The expense endpoint also retains its own stream bound.
- Added cross-site Fetch Metadata checks to Museum and expense, alongside Origin checks. Municipal already had these checks. Trusted Host validation remains in all three.
- Restricted Museum reset to MUSEUM-DEMO cohorts and rejected unknown request fields. Regression tests explicitly try to reset a foreign cohort and verify owned reset leaves the foreign record intact.
- Preserved approval gates, stale-version handling, idempotent execution and lost-response recovery in procurement examples. Municipal additionally uses a reset manifest and exact cohort confirmation.
- Unified CI across all three packages on Python 3.11 and 3.14, with repository read-only permissions and no deployment steps.

Local verification: Municipal 13 tests; Museum 9 tests; expense 11 tests plus 5 unittest subtests. All passed on Python 3.14. TestClient emits an upstream httpx deprecation warning; it does not fail tests. GitHub CI supplies the separate 3.11 verification.

## Boundaries and remaining limitations

These are single-user loopback demos. Museum and Municipal use per-process browser session tokens, not user identity. Demo reviewer personas do not enforce separation of duties. The expense calculator is stateless and has no login. Anyone with local machine access may access these demos. Do not bind them to a public interface or put them behind the public reverse proxy without a separate authentication, authorization and deployment review.

Swagger uses FastAPI's hosted documentation assets; the application UI runs from bundled local assets, but Swagger requires network access. There is no provider API usage or associated provider charge from simulated operations. A security audit cannot promise absence of every issue.

Museum intentionally displays only the first 100 records while export covers the full generated cohort. Municipal has searchable pagination. Neither demonstrates real ERP writes. Shared examples use original generic artwork; retained font licenses remain in each package.

Git-ignored local-dev Studio, API Blaster, source archives, personal reports, runtime databases, secrets and virtual environments are excluded from this publication. This review does not certify those experimental tools. In particular, any experiment capable of redirecting to a real Maestro trigger needs an explicit live-operation boundary before graduation.

## Graduation checklist

1. Keep synthetic fixtures and locally owned reset scope.
2. Declare simulated versus live behavior visibly; no silent live fallback.
3. Require explicit preview, authorization and confirmation before enabling real writes.
4. Test replay, partial failures and reconciliation before enabling retries.
5. Add source/asset attribution, installation steps and independent tests.
6. Exclude environment files, keys, databases, logs and generated runtime files.
7. Run tests and dependency audit, then publish only named reviewed files.

## Generic identity publication — 2026-10-09

Renamed packages to NFP, Museum and Municipal types; replaced identifying visual assets with original generic SVG/CSS; removed the old branded screenshot and organization-specific research links. Regenerated diagrams without embedded source metadata and rebuilt the report. Actual organization policies are replaced by explicitly synthetic assumptions. Required third-party font attribution is retained. Prior commit/branch/PR history remains outside this current-tree cleanup. Existing databases/environments are not migrated automatically.
