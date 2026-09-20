# Live PUG architecture explorer

The explorer inspects registered routes and bounded request metadata. It never invokes
webhooks or OAuth to establish health. The existing persisted-event monitor remains at
`/webhooks/monitor/ui`, using its published static JavaScript and polling fallback.

## Enablement and access

The explorer and its tracing middleware are **disabled by default**. Set
`GATEWAY_EXPLORER_ENABLED=1` before application startup to register `/explorer/ui`,
`/explorer/metadata` and `/explorer/traces`. Other values leave them unregistered.

This is an exposure switch, not authentication. Before enabling it on a server, apply
the existing Traefik operator authentication policy to `/explorer` and `/explorer/*`,
including JSON endpoints. Keep the backend inaccessible around that edge policy.
For local use, bind to `127.0.0.1`. Do not rely on absence from navigation as protection.

All explorer responses use `Cache-Control: no-store`. The UI loads same-origin external
JavaScript and CSS, without inline scripts, event handlers or third-party assets. Its
Content Security Policy restricts scripts, styles and requests to the same origin and
disallows framing. Verify the combined policy in the actual enterprise browser; local
checks do not certify the deployed edge's CSP or authentication behavior.

## Local run and tests

From the checkout root, with Python 3.12 available:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m unittest discover -s tests -v
mkdir -p data
GATEWAY_EXPLORER_ENABLED=1 GATEWAY_DB_ENABLED=1 GATEWAY_DB_PATH="$PWD/data/gateway.db" \
  .venv/bin/uvicorn gateway.app:app --host 127.0.0.1 --port 8001
```

Open `http://127.0.0.1:8001/explorer/ui`. Visit `/health`, then refresh Request Trace.
Without a privately configured HMAC key, webhooks fail closed. These commands do not
load production credentials. OAuth tests are mocked; SQLite tests use temporary state.

For image-based verification, build the production Dockerfile, mount the checkout
read-only at `/review` in a disposable container, install
`/review/requirements-test.txt`, and run discovery from `/review/tests`. This tests the
code baked into `/app`, rather than replacing it with a source mount. Test dependencies
are not part of the production image. See [release scope](14_release_scope.md).

## Measurement and limitations

Routes, models, parameters and dependency metadata come from registered FastAPI routes.
The flow diagram is an explicit description of the current implementation, not automatic
internal-call discovery. A registered route is not proof that its integration is healthy.
The dictionary webhook envelope is not a Pydantic EventEnvelope. HMAC runs explicitly
inside the webhook handler. The registered `/docusign/ping` is local; `/docusign/jwt-test`
can make outbound OAuth calls when explicitly requested elsewhere.

Pure ASGI middleware measures request lifetime and response-start time with a monotonic
clock. Named spans cover HMAC, combined ledger work and JWT token/userinfo calls. They
can overlap and must not be added together as separate stages. Streaming lifetime includes
waiting until disconnect; active streams are absent until they complete. Ingress, routing,
Pydantic, individual SQL operations and historical-event durations are not measured.

At most 200 completed traces are retained per worker. Restart clears them; different
workers can return different samples. Explorer and static requests are excluded. Traces
contain no request bodies, headers, tokens, query strings or unmatched raw paths.
The Data view calls the existing protected `/events/latest` API; that API can return
sensitive headers/parsed payload fields even though the explorer displays selected
metadata only. Its access policy must remain intact.

The UI refreshes every ten seconds while visible, unless a request is running or a route
button has keyboard focus. Requests time out after eight seconds; switching views cancels
older requests so late results cannot overwrite the selected view. Trace failures clear
trace results rather than presenting old samples as current. Ledger failure leaves the
architecture available. Values are inserted as text, not HTML.

Ledger persistence remains best-effort and duplicate inserts retain the original row.
The helper's reported event ID may not identify that row. Trace metadata does not cure
these existing custody or deduplication limitations. No schema migration is introduced.

## Presentation scope

This operator inspector follows the existing monitor's neutral palette, with responsive
layout, visible keyboard focus and explicit selected-view state. It does not implement
organization profiles or claim full ADR-0011 conformance. The organization console and
source replicas retain their existing identity contracts; this change does not rebrand them.

## Deployment and follow-up

Use the [Hetzner runbook](11_hetzner_api_ingress.md). Keep the feature off until the
operator route policy is confirmed. A configuration change requires recreation of the
Compose container, not merely a restart. Persistent/cross-worker traces, active-stream
telemetry, canonical duplicate IDs and durable rejection audit remain follow-up work.
