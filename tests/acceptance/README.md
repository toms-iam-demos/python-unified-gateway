# Isolated AMD64 acceptance rehearsal

Use a dedicated local Docker context containing the verified Linux AMD64 image.
The default context is `colima-pug-rehearsal`. Override it with
`PUG_REHEARSAL_CONTEXT` only for another isolated local daemon. The test uses
the exact image ID recorded in the runner, with no pull, network or published
ports. It uses temporary SQLite and removes its container on exit.

With Node and Playwright available, run `bash tests/acceptance/run.sh`.
Set `PLAYWRIGHT_MODULE` to an absolute module path if Playwright is installed
outside Node's normal resolution path. Set `PUG_CHROME_PATH` to use an existing
Chrome executable in place of Playwright's Chromium.

The test sends signed synthetic deliveries through the real image, then checks
the receipt and duplicate identifiers in the monitor feed and SQLite. Browser
requests reach the isolated image through Docker exec. Playwright simulates
the ingress Basic Auth decision using synthetic credentials and blocks external
browser requests. This exercises browser rendering and monitor polling. It
does not validate production ingress, real operator credentials, or SSE.

## Traefik ingress rehearsal

With the isolated Colima profile running, use the following commands to cache
the pinned Traefik 3.6.16 image and run the test. The verified AMD64 gateway
image must already be in the same profile. The runner uses local `htpasswd`
to generate a hash for the synthetic operator.

```sh
docker --context colima-pug-rehearsal pull --platform linux/amd64 \
  traefik@sha256:f79c88ed5252ae1e31c757a9796d751461ddb502437b8d8526db9e12605a82eb
bash tests/acceptance/ingress/run.sh
```

Both containers run on a disposable internal network with no published ports.
The test checks real Traefik Basic Auth and routing, including signed webhook
ingress without operator credentials, rejection of invalid signatures, and one
matching HMAC-verified receipt in temporary SQLite and both operator feeds.
The routes and credentials are synthetic. The test uses HTTP inside the
isolated network and does not validate production routing, TLS certificates
or termination, or browser rendering.

### Browser through Traefik

With the same images and the Playwright setup above, run
`bash tests/acceptance/ingress/run.sh --browser`. Playwright forwards browser
requests over the internal Docker network. Traefik makes the Basic Auth
decision. The check covers anonymous denial, signed webhook receipt and
deduplication, matching monitor and event detail, and truncated raw preview
masking. It uses synthetic routes and credentials over plain HTTP and tests
monitor polling. Production routing, TLS, and SSE are outside its scope.

## Phase 2 release checklist

### Before deployment

- [ ] Record the candidate Git commit, platform, immutable gateway image ID,
  Traefik digest, and rehearsal result. The current runners pin these images:
  - Linux AMD64 gateway:
    `sha256:35690f60beb4d0cc8db6e0895c948c9fb601e4e6421e59cdd5e97d607dfc8928`
  - Traefik 3.6.16, selected for Linux AMD64:
    `traefik@sha256:f79c88ed5252ae1e31c757a9796d751461ddb502437b8d8526db9e12605a82eb`
  A pass applies to the image actually exercised. For a different release
  candidate, review and update the test image pin and rerun the checks.
- [ ] Run `bash tests/acceptance/ingress/run.sh` and
  `bash tests/acceptance/ingress/run.sh --browser` using the isolated setup
  above. Record a pass when all of the following hold:
  - Traefik denies anonymous and incorrect credentials. A synthetic operator
    can load the monitor and event browser, including their feeds and assets.
  - A signed webhook without operator credentials returns HTTP 200 and
    `persisted: true`. An invalid signature returns HTTP 401.
  - The HMAC-verified SQLite receipt matches the monitor and event browser.
    Replaying the delivery leaves one row and preserves the stored event and
    correlation IDs.
  - The event browser opens the matching detail and masks the synthetic
    credential in its truncated Raw body preview.

The rehearsal uses synthetic routes, credentials, and payloads over plain HTTP
on a disposable internal network with temporary SQLite. The monitor check
covers polling. Production routing, TLS, real operator credentials, and
server-sent events (SSE) are outside rehearsal coverage.

### After an authorized cutover

Record each live check as pending until observed.

- [ ] In an authenticated production operator session, verify that the monitor
  loads and displays its feed, and that the event browser opens a receipt's
  detail view. Record the time and outcome for both.
- [ ] Passively observe an organic post-cutover Docusign delivery. Confirm the
  gateway returned HTTP 200 and match the monitor's persisted event ID to an
  HMAC-verified ledger receipt. Record the time and event ID. Leave this check
  pending while waiting for a delivery.

### Clean-room build evidence

On November 8, 2026, an empty disposable Colima Docker environment built
`6c94a01064d5bb9349f6ce6688f3f2bc36ff2acb` with
`docker build --no-cache --pull --platform linux/amd64`. Rosetta provided
AMD64 execution. The resulting image was
`sha256:5dbbcf738ea43fab4e55d7ca8bff13de0115873ce822ce5bc9b064132fec296f`
and ran Python 3.12.12 on x86_64.

Both Traefik acceptance modes passed using the pinned Traefik 3.6.16 image.
Basic Auth rejected anonymous and incorrect credentials. The synthetic
operator could use both views. A valid signed delivery returned HTTP 200
with persistence confirmed, and an invalid signature returned HTTP 401.
The monitor and event browser matched the HMAC-verified SQLite receipt.
Replay preserved one row and the original identifiers. The truncated Raw
body preview masked the synthetic credential.

Scratch copies of the runners pointed to the clean-room Docker context and
fresh image ID. The browser used existing host Playwright and Chrome. Tests
used synthetic routing and credentials, isolated HTTP, and temporary SQLite.
Production routing, TLS, and SSE were outside scope. Test containers and the
network were removed, and the clean-room profile was stopped. This is
rehearsal evidence for the fresh image. The runner pins above identify the
previously verified release artifact.

## Independent operator rehearsal

Use a fresh checkout of the candidate revision and a dedicated, empty local
Docker daemon. On Apple Silicon, one option is a new Colima profile with
`colima start --profile pug-operator --activate=false --vm-type vz --vz-rosetta --disk 20`.
These commands are for the disposable profile. They use no production
credentials, databases, mounts, or endpoints.

1. **Preflight.** Install or make available Git, Bash, Docker and Compose,
   Python 3, bcrypt-capable `htpasswd`, Node, Playwright, and Chromium. Set
   `PLAYWRIGHT_MODULE` and `PUG_CHROME_PATH` as described above if needed.
   Launch and close Chromium once before building. Inspect the context's
   endpoint and confirm it is the new local daemon. Confirm its image store
   and container inventory are empty and its Docker filesystem has at least
   5 GiB available. Pull the pinned AMD64 Traefik image above into that context
   and run its `version` command with `--platform linux/amd64 --network none`
   to verify registry access and AMD64 execution. Stop on any failure.
2. **Build and start.** Use a clean checkout of the source being built. Set
   these variables from the build. Record the commit, image ID, Docker and
   Compose versions, and Traefik digest.

   ```sh
   export PUG_REHEARSAL_CONTEXT=colima-pug-operator
   docker --context "$PUG_REHEARSAL_CONTEXT" build --no-cache --pull \
     --platform linux/amd64 -t pug-operator:candidate .
   export PUG_GATEWAY_IMAGE=$(docker --context "$PUG_REHEARSAL_CONTEXT" \
     image inspect -f '{{.Id}}' pug-operator:candidate)
   docker --context "$PUG_REHEARSAL_CONTEXT" run --rm --pull never \
     --network none --platform linux/amd64 "$PUG_GATEWAY_IMAGE" \
     python -c 'import platform,sys; assert platform.machine()=="x86_64" and sys.version_info[:3]==(3,12,12)'
   ```

3. **Ingress and browser.** Run `bash tests/acceptance/ingress/run.sh` and
   `bash tests/acceptance/ingress/run.sh --browser`. Both use the candidate
   image and verify default startup, health, auth, and operator views.
4. **Delivery and persistence.** Both runners check rejection of an invalid
   signature and successful persistence of a signed delivery. The browser
   runner also matches the ledger receipt to the monitor and browser, and
   verifies deduplication with stable event and correlation IDs.
5. **Masking.** The browser runner checks the stored synthetic body and
   verifies the truncated preview hides its credential.
6. **Recovery.** In the same disposable daemon, build a separate known-good
   Linux AMD64 baseline from a clean checkout, such as
   `6c94a01064d5bb9349f6ce6688f3f2bc36ff2acb`, using the same build command
   with a different tag and source directory. Set `PUG_ROLLBACK_IMAGE` to its
   full image ID. Run `bash tests/acceptance/rollback.sh`. It exercises both
   images with orphan removal disabled, an internal network, and a temporary
   named volume. It checks health, preservation of the historical test
   container, and survival of the synthetic receipt across rollback.
7. **Failure handling and cleanup.** The rollback runner exercises rejection
   of a missing image, recovery after an injected post-start check failure,
   and explicit reporting of a failed rollback verification. It removes its
   Compose resources and checks that none remain. Inspect the disposable
   daemon for leftover containers, custom networks, or volumes and stop it.
8. **Handoff.** Have an operator who did not prepare the runners execute the
   procedure. Record the exact commands, image IDs, results, and any help
   needed. A private input, undocumented override, manual rescue, or failed
   gate leaves handoff open. After a correction, start from a fresh daemon.

The ingress tests cover synthetic HTTP routing and Basic Auth, with monitor
polling. Production routes, TLS, live credentials, organic Docusign traffic,
and SSE are outside this rehearsal.
