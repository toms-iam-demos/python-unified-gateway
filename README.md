# Python Unified Gateway

**A Python and FastAPI integration layer for APIs, events and agreement workflows.**

Python Unified Gateway (PUG) connects enterprise systems through explicit, inspectable integration logic. It runs locally or as a containerized service, with Docusign as its first implemented provider connection.

## Capabilities

- **Verified webhooks** with a persistent SQLite event ledger.
- **Read-only provider and workflow inspection**, with reviewed access boundaries.
- **Event APIs and browser tools** for inspecting requests and recorded results.
- **Optional tracing and operator audit logging** for troubleshooting.
- **A website component** with shared navigation, a searchable catalog and example pages.

Provider operations are deliberately limited. See the [Docusign API guide](docs/006_runbooks/16_full_docusign_api.md) for the supported scope.

## Try a local example

The [example catalog](examples/README.md) includes NFP expense reconciliation, Museum procurement and Municipal procurement. Each uses synthetic data and runs independently with Python and a browser. Provider credentials and a gateway deployment are not required. The catalog includes Windows and macOS setup instructions.

For gateway setup, start with the [local development guide](docs/006_runbooks/10_local-dev.md).

## Hosted demonstrations

The separately managed private runtime adds connected agreement workflows, a Stripe test-payment decline and recovery demo with kickoff tracking, and guided read-only agent examples. Invited guests receive a 24-hour link scoped to one example and Home.

Its operator-only Event Explorer shows a cached snapshot of up to 200 gateway records, with search, filters, payload inspection and manual refresh. It does not poll. Raw JSON endpoints remain available separately.

These hosted extensions are not included in the public local-demo setup. Connected demos, simulations and planned capabilities are labelled separately; they are not a claim of production readiness.

## Project structure

| Directory | Contents |
| --- | --- |
| [`gateway/`](gateway/) | API service, webhook handling and event storage |
| [`examples/`](examples/README.md) | Portable demonstrations with synthetic data |
| [`www/`](www/README.md) | Reusable website source and deployment-profile boundary |
| [`docs/`](docs/) | Setup, architecture, operations and change records |
| [`tests/`](tests/) | Automated behavior and regression checks |

The website source and hosted deployment have separate release boundaries. See the [website ownership note](docs/frontend/www.md) before changing live routes.

## Contributing and operations

Start with [contributing](CONTRIBUTING.md), the [architecture decisions](docs/007_adr/index.md) and the [release scope](docs/006_runbooks/14_release_scope.md). Deployment and security guidance is in the [Hetzner runbook](docs/006_runbooks/11_hetzner_api_ingress.md) and [operator security guide](docs/006_runbooks/17_operator_security.md).

PUG is under active development. Credentials, provider records and private deployment configuration belong outside the public repository.
