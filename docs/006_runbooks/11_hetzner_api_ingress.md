# Hetzner API ingress and release procedure

PUG serves `api.tifirmo.io` behind Traefik, with a SQLite ledger and externally mounted
secrets/state. Preserve that topology. The checked-in Compose service is `ds-gw` and
its internal port is 8001. The server's PUG checkout, overrides, current image and
Traefik rules must be discovered before using this procedure; do not substitute the
local Compose file for the server's existing configuration.

The January operational record identifies server-local `/opt/traefik` configuration.
That is historical context, not proof of the current deployment layout. See
[the preserved operational note](../00_now/2026-01-07-webhook-inbox-and-lockdown.md).

## Release gate

Obtain explicit approval for the reviewed revision before pushing or deploying.
Record the candidate revision, passing Python 3.12 tests and image identity. Confirm
that the release retains the existing monitor/static assets and excludes experimental
tools, local credentials and runtime data. No new database migration is part of this release.

## Inspect the actual deployment

Using the existing authorized server connection:

1. Locate the running PUG container and its Compose project/service. Identify the
   checkout and all active Compose files, networks, port bindings and mounts.
2. Record the running image ID, deployed Git revision if known, local server changes
   and restart policy. Do not overwrite server-local modifications with a pull/reset.
3. Inspect the actual SQLite schema for `verify_status` and `verify_reason`, DB path,
   volume ownership and free space. These columns exist in the checked-in schema,
   but the server schema must be verified independently.
4. Verify the HMAC key is present and nonblank in private service configuration and
   matches the Connect configuration. Never print or paste the value. The public
   webhook must continue to reach PUG without operator Basic Auth.
5. Keep `/webhooks/monitor`, `/webhooks/monitor/*`, `/events/*` and any existing
   protected docusign routes behind their operator policy. Before setting
   `GATEWAY_EXPLORER_ENABLED=1`, protect both `/explorer` and `/explorer/*`, including
   JSON endpoints, through the same policy. Confirm no direct backend port bypasses it.
   If this is not ready, leave the explorer disabled; HMAC does not depend on it.

Do not paste full environment or rendered Compose configurations into reports: they
may contain secrets. Record only the necessary nonsecret evidence.

## Backup and rollback preparation

Keep the current image available by immutable ID or a local rollback tag. Preserve the
current Compose/Traefik configuration and environment files in a private server backup.
Record mount paths and the approved recovery plan.

Make a consistent SQLite backup with SQLite's backup facilities, or stop writes before
copying the database and associated WAL state. Copying only a live main DB file is not
a reliable backup. Check the backup's integrity and access permissions. Record its time
so later accepted events can be accounted for if a restore becomes necessary.

## Deploy the approved revision

Bring the approved revision into the server's established release checkout. Build with
its established Compose invocation, retaining its override files and project settings.
After the private environment and edge policy are ready, recreate the PUG service.
For a deployment confirmed to use the checked-in service name, the core operation is:

```sh
docker compose up -d --build --force-recreate ds-gw
docker compose logs --tail=100 ds-gw
```

Include the deployment's required `-f`/project options in those commands. Do not replace
Traefik, networks, volumes or secret mounts. A plain restart does not load changed
Compose environment values. Do not enable explorer before its route protection exists.

## Verify after recreation

- Check the running image and service status against the intended release.
- Confirm internal and public `/health` return the expected PUG response. Health alone
  does not verify HMAC configuration, the database or provider connectivity.
- Verify unauthenticated monitor/events requests are denied and authenticated monitor
  inspection works, including `/static/monitor.js`, polling and cached event details.
- If explorer is disabled, confirm its routes return 404 at the application. If enabled,
  confirm unauthenticated access is denied at the edge and authorized UI/metadata/traces
  requests work. Inspect browser console/network output for CSP and asset failures.
- Use one approved demo Connect event to prove real signature acceptance and successful
  storage with `verified` / `hmac-sha256`. Confirm provider delivery status and inspect
  the actual stored row, not only an HTTP status or generated trace ID.
- Review edge and application logs for repeated 401/503 responses or database write
  failures. Exercise invalid/missing signatures against an isolated receiver.
- Confirm state persists through the approved restart/recreation check. Do not infer
  persistence from the process-local monitor or trace buffer.

## Recovery

If only the explorer is faulty, unset its flag and recreate PUG while retaining HMAC.
If HMAC configuration is wrong, repair the private configuration and recreate; inspect
provider retries/backlog. Do not silently roll back to accepting unverified requests.

For an approved application rollback, select the recorded previous image and matching
configuration through the existing Compose workflow, preserving data mounts. Recheck
health, auth, monitor behavior and delivery handling. The previous image may lack HMAC,
so agree an ingress containment/retry strategy before restoring it. This is a security
policy reversal, not just a visual rollback.

No schema change requires restoring the database for this release. Restore a backup
only for a demonstrated data problem with an explicit plan for events accepted since
that backup. Finish by recording the running revision/image, verification results and
any unresolved delivery backlog.
