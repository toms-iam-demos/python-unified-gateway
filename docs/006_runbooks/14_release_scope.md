# Release scope and experimental tools

The production application is `gateway.app:app`. Its runtime source, SQL schema and
static assets live under `gateway/`. ADRs use the shared sequence in `docs/007_adr/`;
runbooks live here, and frontend specifications remain in `docs/frontend/`.

## Included in this release

- The deployed persisted-event monitor, summary polling and bounded detail previews.
- Connect HMAC verification before persistence and broadcast, with verification metadata.
- Worker-thread ledger writes and optional, bounded operator telemetry/explorer.
- Relevant tests and corrected canonical documentation.

## Kept outside the release

The original development checkout retains `notebooks/`, `pug/`, `tools/blast/`,
notebook checkpoints and `mkdocs.local.yml`. They were not copied into this release
checkout, moved into runtime packages or deleted. The batch tool remains experimental:
its fresh database needs manual schema initialization; queue selection is not restricted
to the current run; concurrent ownership and partial-success recovery need design and
tests. It must not be used as canonical gateway delivery custody.

Any future inclusion of this tool should define its role under ADR-0002 and ADR-0009,
use a separate tooling database, sanitize templates, and make side effects and retry
behavior explicit. A dry-run queue must not unexpectedly become a later live batch.

## Build boundaries

The Docker build context allows only `Dockerfile`, `requirements.txt` and `gateway/`,
with additional exclusions for accidental local state under that package. The image
copies only the runtime requirements and application package. Git history, environment
files, secrets, SQLite state, authoring tools and documentation do not belong in it.
The existing external Compose data and secret mounts remain unchanged.

`requirements-test.txt` adds TestClient's httpx dependency for disposable test environments;
it is not installed into the production image. Public documentation uses `mkdocs.yml`,
which explicitly excludes local genesis and checkpoint material even if those files
exist in a developer's checkout. Build with `mkdocs build --strict` before publication.

A production release still requires the checks in the [Hetzner runbook](11_hetzner_api_ingress.md),
especially HMAC configuration and operator access. Passing local tests is not production
verification or authorization to deploy.
