# Duplicate deliveries return stored ledger identifiers

- Date / timezone: 2026-11-08, America/Los_Angeles.
- Actor and authorization: Codex, explicitly authorized by the maintainer to implement the smallest fix, review it, and commit locally.
- Baseline commit: `78e3dbe6e879dd52cc1a879d9ffc197006eed988`.
- Scope: `gateway/db/events_store.py` and `tests/test_duplicate_delivery_identifiers.py`, plus this validation record.
- Behavior: when INSERT OR IGNORE inserts no row, retrieve identifiers using the existing unique key (source, kind, dedupe_key) on the same connection before commit. Return the original event and correlation identifiers without updating the stored row. If no matching row exists, retain the existing degraded-persistence error response rather than claim success.
- Safety review: parameterized lookup matches the schema's deduplication constraint; no schema, route, authentication, dependency or deployment changes. Existing insertion and fail-open webhook policies remain unchanged. The regression uses synthetic input and temporary SQLite, restores environment/schema-cache state, verifies one row, and checks both deliveries against stored identifiers even when the retry supplies a different correlation ID.
- Validation: the regression failed before the fix on duplicate identifiers and passed afterward. `python3 -B -m unittest discover -s tests -p test_duplicate_delivery_identifiers.py -v` passed (1 test), including a final review rerun.
- Additional checks passed during implementation: three ad hoc temporary-SQLite checks covering preservation of legacy verification metadata, distinct payload/source rows, and disabled persistence creating no database; `python3 -B -m unittest discover -s tests -p test_public_identity.py -v` (5 tests); `python3 -B tools/check_public_identity.py` (zero failures); `node tests/test_monitor_ui.cjs`; and `git diff --check`.
- Initial test gap (resolved): the first validation used Python 3.14 and could not run the FastAPI suites because that environment lacked dependencies. Subsequent maintainer-authorized validation created a disposable Python 3.12.12 environment outside the repository and installed `requirements-test.txt`. All 24 explicit runtime/test pins were verified and `python -I -B -m pip check` reported no broken requirements. Repository dependency files were unchanged.
- Final Python 3.12.12 validation of fix commit `2c90075`: all 34 tests passed: duplicate identifiers (1), HMAC (13), explorer (10), monitor bounds (4), webhook concurrency (1), and publication identity (5). An in-memory unittest runner used `loadTestsFromNames` for `test_duplicate_delivery_identifiers`, `test_connect_hmac`, `test_explorer`, `test_monitor_bounds`, `test_webhook_concurrency`, and `test_public_identity`, under the disposable interpreter with `-I -B`. SQLite connections were restricted to temporary storage, test configuration was synthetic, provider calls were mocked, and network access was blocked during testing. Zero prohibited-access attempts were detected; temporary databases were cleaned up.
- Dependency-drift reconciliation: an earlier existing Python 3.12.12 environment ran 29 tests with 27 passing and two explorer errors. Its FastAPI 0.162.0 changed included-router representation and removed the field `type_` interface used by explorer introspection. Both explorer tests passed with the pinned FastAPI 0.122.0 / Starlette 0.50.0 environment; no explorer code change was needed.
- Initial validation limitations: the pinned Python 3.12.12 run closed the local dependency gap. Subsequent production-source reconciliation and isolated container/browser evidence are recorded below; no deployment or real provider transaction has been performed.
- Documentation follow-up: explicitly authorized to record the final results and commit documentation locally, without runtime changes, push or deployment.
- Recovery of the repository fix: revert `2c90075` to restore prior duplicate-identifier behavior; reverting documentation commit `1dde586` alone does not change runtime behavior. No database restore or migration is required. No production backup was created because production state was not changed.
- Publication / release: local commit only; no push, deployment, provider calls or production changes.
- Notion mirror: not requested.


## Production-preserving rehearsal evidence

These results are local evidence, not publication, deployment approval or a claim of complete production equivalence. Recorded on 2026-11-08 (America/Los_Angeles).

- Source reconciliation found server checkout `6ea1bca7ccc073bcf223220419a5a907f509ba56` on main, but the running application contains additional event-browser/snapshot assets and presentation middleware. Do not rebuild the older local checkout or incomplete server checkout as a replacement for the running application.
- Observed running image: `python-unified-gateway:standard-navigation-20261104-r1`, immutable ID `sha256:762830c003fe89cc25fdbfbafdeaf933d76dc5da56ed5b46de0a7a445059e3b3`. It had no source-revision label. Reconfirm this identity before any release because observations can become stale.
- An isolated candidate outside this repository preserves the captured running source and assets. Its only runtime differences from that capture are the duplicate fix in `gateway/db/events_store.py` and the separately authorized masking fix in `gateway/event_explorer/app.js`. The masking fix and its test exist only in that candidate; they have not been incorporated into this repository or published.
- Installed production package metadata differed from its bundled requirements file. The rehearsal reproduced all 32 captured installed package versions and added HTTPX 0.28.1 for tests. Package-version assertions and pip consistency checks passed. Do not silently replace this observed dependency set with either checkout's requirements during release preparation.
- Native Linux ARM64 rehearsal passed the duplicate regression, with 32 of 34 existing Python tests passing and all four additional production-behavior checks passing. Initial AMD64 execution failed before application startup because the local emulator could not execute the image shell.
- Rosetta was enabled only in the separate local rehearsal profile. AMD64 shell and Python 3.12.12 execution then succeeded. The AMD64 rehearsal repeated the 32/34 Python result and four passing production-behavior checks with no new failures. The two existing failures expect anonymous JWT-test access and explorer-relative paths for shared presentation assets; both reproduced against unmodified captured production persistence. They are explicit baseline/test-assumption exceptions, not a green full-suite result.
- The masking defect was reproduced with a 4,000-byte synthetic truncated raw JSON preview: a synthetic token remained visible with personal masking on or off. Complete JSON controls passed. Captured production and candidate masking source were identical before the fix.
- The candidate masking fix conservatively omits incomplete JSON previews containing credential fields, or unparseable quoted field names, and displays a redacted notice. It does not rewrite stored data. Valid JSON handling, ordinary raw text, personal masking controls and payload bounds retain their existing behavior. This is a display safeguard, not a guarantee that every arbitrary secret can be detected or that raw-record APIs redact data.
- All 12 synthetic masking tests passed with Node's built-in test runner (`node --test tests/test_event_browser_redaction.cjs` in the isolated candidate). The monitor JavaScript behavior checks passed. Five Python temporary-SQLite checks covering monitor bounds and duplicate identifiers passed.
- The rebuilt AMD64 candidate again verified all 32 captured production package versions, passed 32/34 existing Python tests and all four production-behavior checks, and reproduced only the two documented baseline exceptions. Local rehearsal image: `sha256:0f331136dbeaacbaecb70615f3fd96eb332abae1b7f43b5346c8a7a2dedd38c8` (`pug-duplicate-rehearsal:amd64-masked`). This is a test image containing test tooling, captured source archive and HTTPX; it is not the approved production release image.
- Browser checks used 205 synthetic records in temporary SQLite: monitor 80-row cap, 16,000-byte detail limit, selection, Clear UI and refresh; event browser 200-row cap, 4,000-byte previews, correlation search, source/result filters and selection retention. Both preserved previous results and displayed stale-data warnings when the local server stopped. All 205 rows and the original 30,159-byte fixture remained intact. The rebuilt candidate hid the synthetic token in the actual browser with personal masking both enabled and disabled.

## Ingress and visual evidence

- Read-only live checks confirmed HTTP-to-HTTPS redirection, HSTS and anonymous 401 responses for operator pages and protected shared presentation files. Public logos, favicon and gateway static assets returned 200. No provider endpoints were exercised.
- An existing authenticated operator browser session rendered documentation and explorer with shared styling and all five branding images loaded, without captured warnings/errors. Redoc redirected to documentation. Live monitor/event-browser pages were deliberately not opened: their event-reading paths can initialize schema.
- Local AMD64 visual comparison ran captured baseline and candidate with identical synthetic databases and local copies of shared CSS, JavaScript, branding and Swagger assets. All ten served files matched their local copies byte-for-byte. No shared presentation source was changed.
- At desktop 1512 x 862 and narrow 390 x 844 viewports, documentation, explorer, monitor and event-browser baseline/candidate measurements matched for layouts, fonts, colors, navigation, branding and image dimensions. Screenshots were visually inspected; copied images loaded and checked console logs had no warnings/errors. Dynamic timestamps differed as expected. This was not an exhaustive pixel-diff test of every interaction, browser or viewport.
- The deliberate content difference was confirmed: the baseline displayed the synthetic token in truncated raw JSON; the candidate displayed its redacted notice.
- The local-only wrapper remapped live-origin/CDN URLs to local copies and used a test-only browser policy to block external resource access. These checks do not revalidate production CSP, authenticated edge routing or external navigation destinations. Swagger's floating CDN v5 assets were copied at verification time; their availability/version remains an external production dependency unless separately addressed.
- Temporary containers/databases were removed and the rehearsal VM stopped after each completed rehearsal. The original Docker context was preserved. No provider calls, production edits, backups, restarts, push or deployment occurred. The copied source/assets, local candidate and test images remain outside the repository for review.

## Proposed final cutover and rollback plan

**Status: not authorized for execution.** This plan requires a reviewed production release artifact and explicit approval before any server write, backup, service recreation or routing change. No guarantee of zero interruption is made.

### Release gates

1. Reconcile current remote main, the server checkout and the captured running source through the repository's normal review process. Preserve production-specific event browser/snapshot, presentation middleware, operator authentication, workflow/full-API registration, audit behavior and static assets. Preserve unrelated services. Do not reset or replace either checkout to obtain a release baseline.
2. Promote the reviewed production-preserving source and both narrowly scoped fixes into a canonical, portable release revision with tests and manifests. Inspect staged content for private state/credentials and run required publication checks. Commit/push/PR/merge remain separate authorized steps; none is implied by this record update.
3. Produce a runtime-only Linux AMD64 release image, excluding rehearsal wrappers, fixtures, tests, source archives and local tools. Pin/record the approved base image digest, Python version, complete resolved package versions and source/asset hashes. The rehearsal image ID is evidence only, not the deployment target. Rerun relevant isolated checks against the actual release artifact and explicitly review the two baseline test exceptions rather than silently ignoring them.
4. Re-inventory the actual running image, source/configuration, mounts, feature flags, network and port binding immediately before cutover. Abort if they differ unexpectedly from the reviewed baseline. Verify actual database schema without calling schema-initializing endpoints; confirm no migration is needed. Confirm capacity for the approximately 4 GB event database, audit database, verified backups and both images; actual free space and backup duration remain unverified.
5. Preserve `traefik-network`, loopback-only port 8001, existing Compose/project overrides, secret mounts, operator login policy and rate limits, explorer/workflow/full-API/audit flags, and the shared presentation services. Preserve the event DB at `/app/data/gateway.db` and audit DB at `/app/data/security-audit.sqlite3` through their existing data mount. Keep public verified-webhook ingress reachable without operator Basic Auth. Do not change HMAC policy or expose a new backend port.
6. Agree the interruption window, verification owner, abort conditions and maximum verification time. Establish actual provider retry/delivery behavior without assuming it. A single-container recreation can interrupt requests; if uninterrupted service is mandatory, stop here until a separately reviewed availability strategy exists. Do not introduce concurrent production writers or an improvised blue/green switch during this release.

### Recovery preparation, after separate approval

1. Retain the exact currently running image by immutable identity and preserve the existing server checkout state, Compose/Traefik configuration and private environment/secret files in access-restricted backup storage. Do not print credentials or delete existing backups.
2. Back up both event and security-audit SQLite databases with consistent SQLite backup facilities, or an explicitly approved writer pause and complete DB/WAL handling. Never copy only a live main database file. Record start/end timestamps; if cross-database alignment is required, agree an appropriate coordinated write pause because independent online backups do not provide a shared transaction snapshot.
3. Check integrity on backup copies, confirm permissions/checksums and demonstrate isolated restoration without contacting providers. Record the recovery point and how events/audit entries accepted after it would be reconciled. Abort cutover if backups, capacity, image retention or recovery evidence are incomplete.

### Approved cutover sequence

1. Obtain approval for the exact release revision, immutable release image, configuration, interruption strategy and rollback image. Transfer only the reviewed runtime artifact through the established release process; do not patch the running container or overwrite shared services/configuration.
2. Recreate only the confirmed gateway service using its established Compose project/files, substituting the approved immutable image while preserving all data/configuration/network invariants. No build-from-stale-checkout operation, migration, Traefik recreation, dependency upgrade or feature-flag change belongs in this cutover.
3. Verify running image identity and process health. Inspect persistence/audit errors and confirm expected mounts, network, port binding and access controls before broader inspection. `/health` is a liveness check only; `/health/ready` and event readers may initialize schema and are not read-only preflight probes.
4. With an authorized operator session, repeat documentation, explorer, monitor, event browser, shared-asset and browser-console checks under the actual production CSP. Confirm anonymous protected paths remain denied and public static behavior is unchanged. Do not execute provider operations. Monitor/event reads and passive observation of legitimate incoming deliveries must be explicitly included in the approved production verification scope.
5. Demonstrate duplicate persistence and masking with synthetic data in isolation against the exact release image. Passive production delivery/storage evidence may supplement this; health or an HTTP 200 alone is not proof of durable custody. A real provider test/event requires separate authorization. Observe for the agreed interval, recording errors, latency and delivery backlog against the pre-cutover baseline.

### Abort and rollback

1. Abort before cutover for unreviewed source/config drift, incomplete recovery preparation, failed release-artifact checks or an unresolved interruption strategy.
2. Roll back during the agreed verification window for new persistence/audit failures, authentication or ingress regressions, missing operator pages/assets, material service degradation, or unexpected behavior beyond the two approved fixes. Record the trigger and time; do not disable HMAC/authentication, expand port exposure or improvise repairs.
3. Restore the recorded pre-cutover immutable image and matching configuration using the established gateway-only Compose procedure. Retain current data mounts. Recheck image identity, health, access controls, presentation and persistence/audit behavior.
4. An application-only rollback requires no database restore. Restore data only for demonstrated corruption with a separately approved reconciliation plan for everything accepted after the backup. Never overwrite newer event/audit history merely to undo an application change.
5. Rolling back to the captured current image reintroduces both the duplicate-identifier defect and the known truncated-preview masking defect; report this explicitly. Retain backups and both images until separately authorized cleanup. Record the final image/revision, checks, outstanding backlog and any unresolved risk; do not claim merged or deployed without evidence.

## Current handoff

The duplicate fix is locally committed in this repository; masking and production-preserving integration remain in the isolated candidate. The AMD64 and visual rehearsals support review but are not release authorization. This documentation update is not committed or published. No runtime files were changed by this update; no provider calls or production actions were taken.


## Local release-source follow-up

A separate release-source checkout has now been prepared from fetched main `6ea1bca7ccc073bcf223220419a5a907f509ba56`. It restores the captured production-only runtime files and includes both fixes. The original checkout's evidence edits remain preserved. See `2026-11-08-production-preserving-release.md` for the source/package manifest, full 67-test Python result, 25 JavaScript tests and remaining image-build/release gates. The earlier “isolated candidate only” and two-test-exception statements describe their historical rehearsal stage; this release-source checkout incorporates the fixes and has passing production-aware tests. No provider call, production action or publication occurred.

## Final production cutover and acceptance

**Status: deployed and accepted on November 8, 2026.** PR #25 merged at `6be7211cf42915c9c8ec4334f821028941a51b3f` from reviewed release commit `6149b83`. The gateway started at 3:56:10 p.m. Pacific on the staged Linux AMD64 image `sha256:35690f60beb4d0cc8db6e0895c948c9fb601e4e6421e59cdd5e97d607dfc8928`. This section supersedes the historical handoff status above.

- **Release evidence.** The actual Dockerfile image used Python 3.12.12 with 32 production package versions verified. Rehearsal passed 67 Python tests, 9 subtests and 25 JavaScript tests, plus runtime startup and visual-parity checks. Duplicate delivery IDs and truncated JSON masking were verified with synthetic data, temporary SQLite and mocked providers.
- **Recovery.** Both SQLite databases had verified isolated restores. Before deployment, the event archive matched its SHA-256 and the isolated event restore passed SQLite quick_check. The audit backup passed integrity and foreign-key checks. The live data mount was preserved. The server journal archive was retired after checksum and gzip verification of the encrypted local copy. After deployment, 2.578 GB was free against a 2 GB reserve.
- **Cutover.** Gateway health passed over loopback and public HTTPS. The monitor UI, assets and feed responded. The event browser UI, assets and live ledger snapshot responded, and public unauthenticated protected routes returned HTTP 401. The operator subsequently confirmed both the monitor and event browser in the signed-in production Firefox session.
- **Docusign.** The read-only configuration lookup confirmed IAM Demos Connect configuration `22020120` was active and unpaused, with SIM, logging and Require Acknowledgement enabled, targeting `https://api.tifirmo.io/webhooks/docusign`. At 4:01:42 p.m. Pacific, the first observed post-cutover delivery returned HTTP 200. The monitor reported persistence and matched the HMAC-verified SQLite receipt `87b5891b-83cd-4a91-8bbd-2f0576e745bd`. No webhook was triggered for verification. Interruption retry behavior was not exercised.
- **Rollback and side effect.** Rollback was unnecessary. The original image `sha256:762830c003fe89cc25fdbfbafdeaf933d76dc5da56ed5b46de0a7a445059e3b3` remains available under `python-unified-gateway:rollback-762830c003fe`. Compose unexpectedly removed ten historical gateway containers from the same project. The designated rollback image and verified backups remained available.

The cutover acceptance checks are closed. Further Phase 2 production work requires its own scope and approval. This closeout is a local documentation update.

### Repeatable AMD64 acceptance rehearsal

The test-only rehearsal passed on the verified image above using Python 3.12.12, temporary SQLite, synthetic signed deliveries and a network-disabled container. Both deliveries returned HTTP 200 with persistence confirmed. The duplicate left one HMAC-verified ledger row and both monitor receipts reported the original identifiers. The browser showed the matching monitor row and event detail, and its truncated Raw body preview hid the synthetic credential. The harness simulates ingress authentication and tests monitor polling. Production ingress authentication, real operator credentials and SSE are outside this rehearsal. See `tests/acceptance/README.md` for the local runner.

### Isolated Traefik ingress acceptance

Traefik 3.6.16 and the verified gateway image passed on Linux AMD64. Anonymous
and incorrect credentials received HTTP 401 on the monitor and event browser
pages, feeds, and scripts. The synthetic operator received HTTP 200. The
webhook route allowed requests without operator credentials, rejected invalid
HMAC with HTTP 401, and accepted a valid signature with HTTP 200 and confirmed
persistence. Both operator feeds matched the single HMAC-verified receipt in
temporary SQLite. Bounded polling accounts for the event-browser snapshot
refresh cooldown.

The test uses a synthetic Traefik routing configuration and plain HTTP on an
isolated internal network. Production routing, TLS, and live traffic are
outside its scope. Run it with `bash tests/acceptance/ingress/run.sh` after
preparing the pinned images as described in `tests/acceptance/README.md`.

### Browser acceptance through Traefik

The Linux AMD64 gateway and Traefik 3.6.16 passed the combined browser
rehearsal. Anonymous requests to both operator pages received a Basic Auth
challenge, and the synthetic operator could load both pages. A signed webhook
without operator credentials returned HTTP 200 and persisted. An invalid
signature returned HTTP 401. Replay preserved one HMAC-verified SQLite
receipt and the browser showed its matching event ID. The truncated raw body
preview hid the synthetic credential.

The test uses synthetic routing and plain HTTP on an isolated network.
Production routes and TLS are outside its scope. The monitor check exercises
polling and does not cover SSE.

## Clean-room image cutover

On November 8, 2026 at 9:29:18 p.m. Pacific, the gateway started on the
qualified Linux AMD64 clean-room image
`sha256:5dbbcf738ea43fab4e55d7ca8bff13de0115873ce822ce5bc9b064132fec296f`,
built from main at `6c94a01064d5bb9349f6ce6688f3f2bc36ff2acb`. Both refreshed
SQLite backup checksums and isolated restore checks passed before recreation.
Orphan removal was disabled and the inventory of other project containers
was unchanged. The prior image `35690f60beb4` remains available for rollback.
No rollback was needed. Free space after cutover was 3.717 GB against a 2 GB
reserve.

- **Gateway and ingress passed.** Loopback and public HTTPS health passed.
  Mounts, network and port binding matched the pre-cutover baseline. Monitor
  and event browser pages, assets and feeds responded. Unauthenticated public
  requests to protected routes returned HTTP 401.
- **Authenticated operator checks passed.** The operator confirmed the
  production monitor and event browser in the signed-in browser session.
- **Organic Docusign delivery passed.** At 9:38:53 p.m. Pacific on November 8,
  the gateway returned HTTP 200 for a naturally occurring delivery. The
  monitor reported persistence and its event ID matched HMAC-verified ledger
  receipt `b09ccf0f-37f4-4b4d-b38b-d0dba3712ba6`. No webhook was triggered
  for verification. The live cutover acceptance checks are closed.

### Independent operator rehearsal preparation

On November 9, 2026, a fresh disposable Docker profile exercised gates 1–7
from the acceptance README. The source was main at
`13c852812549a562bf68d8913278de88ba59b73e`. The no-cache AMD64 build produced
`sha256:3d629400f3440da8797011ebaf8cab589bfd1c2f3b2a891031f6f7c0433b8f8d`.
Python 3.12.12, Traefik HTTP and browser checks, receipt matching,
deduplication, and masking passed. The rollback baseline was rebuilt from
`6c94a01064d5bb9349f6ce6688f3f2bc36ff2acb` as
`sha256:629efd9d23a6f0ec4fad137b9f64223ebf4d23509fa1a908379aad6e676bb9a3`.

The first attempt stopped at preflight due to a shell quoting error in the
disk check. The corrected run restarted from the empty image store and passed
the technical gates. The missing-image case left the gateway unchanged.
The injected post-start failure restored the baseline and preserved the
synthetic receipt and historical container. The injected rollback
verification failure returned the expected explicit failure result.
No containers, custom networks, or volumes remained in the rehearsal daemon.

The runners now take documented image and context inputs. Gate 8 remains
open until an operator who did not prepare them executes the procedure.

### Gate 8 independent operator sign-off

On November 9, 2026, the operator independently completed the documented
rehearsal and confirmed that no undocumented overrides, assistance, or
manual recovery were needed. Gate 8 passed.

The run used candidate revision
`347124c85c5944bc4a37b41ddc0c12291d60258a` and rollback source
`6c94a01064d5bb9349f6ce6688f3f2bc36ff2acb`. Both AMD64 builds succeeded.
The candidate image was
`sha256:0ad79c5a90ccfe70537524cf566ef6667a8af9eade1be0d9133a1e55aea1cccb`
and the rollback image was
`sha256:175b3b108b7a5fd601da2e9a9477655f87db8bffd0be8fee76c452c586ac8f16`.

Review of the run log and both build logs confirmed preflight, Traefik
authentication, operator browser views, signed receipt matching, duplicate
identifiers, and masking. The missing-image and rollback-verification
faults produced the expected results. Rollback preserved the synthetic
SQLite receipt and the historical test container. The final inventory had
no containers, custom networks, or volumes, and the disposable profile
shut down successfully. This closes the independent rehearsal gate within
the synthetic scope described in the acceptance README.
