# Local production-preserving release source

- Date / timezone: 2026-11-08, America/Los_Angeles.
- Authorization: establish canonical release source locally, preserving current production behavior and including only duplicate-identifier and truncated-preview masking fixes. No provider calls, production changes, push or deployment.
- Git baseline: fetched GitHub main `6ea1bca7ccc073bcf223220419a5a907f509ba56`, matching the previously observed server checkout. Fetch is repository discovery, not a provider API call. A separate independent local checkout was used after managed-worktree setup did not complete. The original checkout and its uncommitted evidence record were preserved.
- Branch: `release/production-preserving-duplicate-masking`.
- Production reference: captured image `sha256:762830c003fe89cc25fdbfbafdeaf933d76dc5da56ed5b46de0a7a445059e3b3`. Its exact Git revision was not recorded in the image. The capture is evidence of observed behavior, not a newly asserted deployed commit or proof of current state.

## Scope and provenance

`release/production-source-manifest.json` contains SHA-256 hashes for every captured gateway file, every release gateway file and the 32 observed installed production package versions. A complete tree comparison confirms that only these runtime files differ from the captured application:

- `gateway/db/events_store.py`: duplicate inserts return the stored event and correlation identifiers.
- `gateway/event_explorer/app.js`: incomplete JSON containing credential fields, or unparseable quoted field names, is omitted behind a redacted notice. Stored data remains unchanged.

The difference from GitHub main is necessarily larger: restore the already-running event browser, snapshot cache, presentation middleware, event-browser assets and their application wiring. These are existing production behavior, not additional feature development. Existing API specifications, operator checks, workflow/full-API flags, security audit, route inspection compatibility, monitor and other assets are preserved byte-for-byte against the captured application.

The shared presentation service's copied files are NOT incorporated into the gateway. Its existing URLs remain external deployment dependencies, as in production. No rehearsal wrapper, captured source archive, temporary database, fixture seed, private configuration, credential, copied cross-service asset or Finder sidecar is added to the source/build context.

## Packaging

- `requirements.txt` pins the complete 32-package observed production installation, including crypto and transitive dependencies. This replaces partial declarations without upgrading captured package versions. HTTPX and pytest remain test-only through the existing test requirements.
- Docker uses the verified registry Linux AMD64 Python 3.12.12 manifest: `python:3.12.12-slim@sha256:42f1689d6d6b906c7e829f9d9ec38491550344ac9adc01e464ff9a08df1ffb48`.
- The existing Dockerfile's extra setuptools installation is removed because setuptools was absent from the captured installed package inventory. Pip remains pinned at captured version 26.2. Existing runtime command, port and copy boundaries are preserved.
- Docker context exclusions additionally reject Finder sidecars and SQLite filename variants. No Compose or ingress files are changed.
- This packaging is prepared source, not a built production release artifact. Its actual Dockerfile build and isolated AMD64 checks have now passed as recorded below; release approval remains separate. The OS packages installed by apt are not fully locked; this is not a bit-for-bit reconstruction of the running image or a claim that its Python/OS build is identical.

## Tests and review

- Both regression tests are included: temporary-SQLite duplicate identifiers and 12 synthetic JavaScript masking cases.
- Existing main already includes the operator override needed by its mocked JWT explorer test. The explorer asset test is updated to assert the exact three shared asset URLs and the exact two gateway-owned asset URLs separately, requesting only gateway-owned files through TestClient. No authentication or routing check is relaxed and no runtime code is changed for the test.
- All 32 captured production package versions were verified in the disposable Python 3.12.12 test environment. The repository-pinned pytest 9.0.3 runner was added only to that disposable environment for existing audit/API tests; no production environment or dependency set was changed.
- Full Python test inventory: **67 passed, 9 subtests passed**, using pytest with cache generation disabled, a temporary base directory, synthetic environment configuration, an outbound-network audit guard and SQLite restricted to temporary storage. Unmocked Requests transport was blocked. Zero prohibited-access attempts occurred. Provider-facing tests used their synthetic mocks.
- JavaScript: **25 passed** across the masking and existing workflow-session tests, plus the monitor behavior checks passed (summary polling, overlap prevention, row limit, bounded detail, stale selection and clear).
- One existing Starlette deprecation warning remains for HTTPX TestClient. Do not install HTTPX2 or alter production dependencies merely to suppress it in this release.
- Prior AMD64/browser/visual evidence is in `2026-11-08-duplicate-delivery-identifiers.md`. Those rehearsals used the same gateway runtime bytes as this source (except the deliberate before/after masking comparisons). The canonical packaging files were subsequently built and checked locally as recorded below; no production cutover occurred.
- Publication identity and whitespace checks must pass on the final staged source; inspect the full staged paths/diff separately for private state. CI and publication are not claimed.

## Recovery and release gates

This is a separate local source checkout. The original checkout and isolated rehearsal candidate remain available. Abandon or revise this local branch to undo source preparation; no production or database recovery is required. Do not replace the running application with the older original checkout.

Before deployment: follow the normal PR/CI process when authorized; verify ingress and shared assets with the approved artifact and configuration; re-inventory actual production; verify consistent event/audit backups and retained rollback image; agree interruption/verification/rollback criteria; then obtain approval for the exact revision/image/configuration. The detailed proposed cutover and rollback plan remains in the linked change record. No production backup, migration, provider action, restart or deployment is authorized by source preparation.

- Status: local release source and AMD64 verification recorded. Publication and deployment remain pending.
- Notion mirror: not requested.


## Canonical image build follow-up

The first actual-Dockerfile attempt exposed an incorrect architecture pin in local source preparation: `f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c` identified ARM64 locally and the build fetched ARM64 OS packages despite the requested AMD64 target. That build was stopped and was not accepted as an AMD64 release. Registry manifest inspection identified `42f1689d6d6b906c7e829f9d9ec38491550344ac9adc01e464ff9a08df1ffb48` as Linux AMD64; a pull and image inspection verified the architecture before correcting Dockerfile and source manifest. This is a local packaging correction only; gateway runtime hashes and production remain unchanged.


### Verified actual Dockerfile result

- Local runtime image: `pug-canonical-release:amd64-local`, immutable ID `sha256:35690f60beb4d0cc8db6e0895c948c9fb601e4e6421e59cdd5e97d607dfc8928`.
- Image inspection verified Linux AMD64, and execution verified x86_64 / Python 3.12.12. Exact installed Python inventory matched all 32 captured production packages with no extras or missing packages. Every runtime file matched the release source manifest; `/app` contained only those files and `requirements.txt`. No tests, fixtures, source archives, credentials, environment files or rehearsal wrappers were baked into the runtime application directory. Pip consistency check passed.
- A separately derived test-only image added HTTPX/pytest without modifying the runtime image. Tests were mounted read-only at `/app/tests` and `/app/tools`, so gateway imports and bounded-event SQL tests used the runtime image's `/app/gateway` files. Full results: **67 passed, 9 subtests passed**, one existing Starlette TestClient deprecation warning. Network was disabled; SQLite was restricted to temporary storage; providers were mocked and unmocked Requests transport blocked. Zero prohibited-access attempts occurred.
- The runtime image's unchanged Uvicorn CMD was exercised directly with all observed feature flags enabled, no external network, a read-only filesystem and temporary SQLite. Checks passed for health, operator rejection, all 424 full-API operations registered, documentation/explorer/monitor/event-browser routes and assets, restrictive explorer CSP, signed synthetic duplicate deliveries producing one stored row and original identifiers, cached snapshot and masking asset. No real credential or provider request was used.
- All 25 JavaScript masking/workflow-session tests and the monitor behavior checks passed again on source verified byte-identical to the image. Node was not added to the runtime image. Publication identity and whitespace checks passed.
- The production OS/Python build has not been established as byte-identical to this image. Debian packages are resolved at build time and not fully locked; actual production ingress, backup/cutover, delivery backlog and high-volume performance remain separate release gates.
- Test containers and their temporary databases are removed and the separate rehearsal VM is stopped after verification. Images are retained locally for review. The verification was performed before the local release commit. No provider calls, production changes, push or deployment occurred.
