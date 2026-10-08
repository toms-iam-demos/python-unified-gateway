# Implementation map

This is a local simulator, not a docusign or SAP connector. The technical report distinguishes verified public context, proposals and implemented behavior.

| Module | Responsibility |
| --- | --- |
| `app/domain.py` | Four versioned synthetic fixtures, decimal arithmetic, evidence gates and date/timing calculations |
| `app/main.py` | Local HTTP API, SQLite transactions, version checks, immutable plans, digest checks, unique inbox receipts, audit and scoped reset |
| `app/static/houston-theme.css` | Houston staff-portal visual layer; city asset and font credits in `BRANDING.md` |
| `app/static/` | Responsive Houston-inspired workspace, research registry, architecture diagrams and API lab |
| `docs/sources.json` | Source register with dates, evidence classifications and implications |
| `docs/*.puml` / `*.svg` | Editable PlantUML and pre-rendered diagrams; Java is not needed to run the demo |
| `tests/test_demo.py` | State transitions, boundary conditions, security boundary and 10,000-record corpus |

## Portability contract

Run a single process bound to `127.0.0.1`. SQLite lives in the ignored `data/` directory. `PUG_HOUSTON_DB` may select another local file for tests. Do not bind to a network interface, expose through a reverse proxy, or use real personal, procurement, sealed-bid or credential data. The UI token protects local API requests against cross-site use; any local user able to open the site can act as the demo reviewer. It is not MFA or segregation of duties.

## Extending a scenario

Add an explicit fixture and evaluator in `app/domain.py`, a typed request field scoped to that scenario, meaningful failure tests, and a view in `app/static/app.js`. Keep money in integer cents and decimal factors in strings. Persist provenance for real extracted values before they can participate in a command. Keep provider-specific payload mapping in a separate adapter; never add an unrestricted pass-through URL or arbitrary provider operation.

## Real integration graduation

A separate sandbox adapter should authenticate docusign inbound calls, validate tenant and resource ownership, resolve read-only agreement references, and create candidate records. Human reviewers must verify extraction against source documents. Add durable event deduplication and an outbox with bounded retries before contacting a remote destination. Discover the actual SAP integration endpoint, permissions, error semantics and receipt facilities with its owner. No endpoint is invented or implied by the local inbox.

Late emergency evidence is retained and warned about rather than erased or backdated. Sending a late review packet must remain possible; it is not authorization to issue an emergency purchase order.

## Reset

Preview `/api/reset-manifest`, export first if desired, then type `RESET <cohort>` and submit the current manifest hash. Only that cohort's fixture records, plans and simulated inbox receipts are removed. Audit entries stay. Real provider deletion is outside this package.
