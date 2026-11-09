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
