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
