# Verification • 2026-10-07

## Passed locally

- Fresh Python 3.14.3 virtual environment with FastAPI 0.142.4, Uvicorn 0.54.0, httpx 0.28.1 and pytest 9.1.1.
- **11 automated tests passed**: authorization and origin boundary; price arithmetic and preparation gates; stale-approval invalidation; single-receipt replay and lost-response recovery; emergency timing boundaries; invoice overage and notice-date calculation; scenario input whitelist; cohort reset; 10,000-record search/pagination/export; all four end-to-end flows; record-level plans beyond the dashboard's latest-100 window.
- One upstream deprecation warning: Starlette's TestClient advises moving from httpx to httpx2. It did not fail the suite; HTTPX is a development dependency here.
- `pip-audit -r requirements.txt`: **no known vulnerabilities found** in the resolved runtime dependency set at check time. This is an advisory scan, not a penetration test or guarantee of future security.
- Canonical LaTeX report compiled successfully with the desktop compiler, including embedded PlantUML-generated TikZ. PlantUML sources also render to SVG for the browser; HTML report is generated from the same LaTeX prose.
- Browser walkthrough: generated 12 records; observed $6,240 price variance; corrected index and saved evidence; prepared and approved a command; injected response loss; replayed and reconciled it. Exactly one local delivery remained.
- Browser architecture diagrams rendered; no console errors observed in that walkthrough.

## Scope and limits

Actual verification was on macOS with Python 3.14.3. Windows instructions are included but were not executed on a Windows machine. A GitHub Actions matrix is supplied for Python 3.11 and 3.14; its remote status is separate from these local results. No real docusign, SAP, Houston procurement system, payment or notification was invoked.

The local inbox shares a SQLite transaction boundary with plans. It demonstrates idempotency/reconciliation semantics; it is not a distributed exactly-once delivery test. No real document extraction, identity-provider integration or policy certification is claimed.
