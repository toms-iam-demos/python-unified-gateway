# Education Fund · Travel reconciliation

A locally runnable, branded Python/FastAPI prototype for travel-expense reconciliation and Maestro notification variables. **Synthetic demonstration, not an official Education Fund system or policy.** No email delivery, bank connection, payment execution, accounting write, file upload, or provider credentials.

## Run on macOS / Linux

Requires Python 3.10+ and internet access for the initial dependency installation. Run these commands from this folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:8087. Stop with **Ctrl+C** in the same terminal. Restart with `python run.py`. To use a different port: `python run.py --port 8090`.

## Run on Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

No shell activation or execution-policy change required. Obtain approval for Python/dependencies through your employer's normal software process if necessary.

## What to try

1. Balanced report: $960 total; C3 $660; C4 $300; $240 card; $720 employee; $200 advance; $520 reimbursement.
2. Funding gap: lodging allocation short by $30. The service identifies the line and holds review readiness.
3. Receipt mismatch: lodging claimed $540, declared receipt $520. No silent correction.
4. Excess advance: $800 advanced against $720 employee expenses yields $80 potential return.
5. Edit any field and reconcile again. Previous results are marked stale until recalculated.
6. Preview the variable-rich Finance message and download the input/result JSON snapshot.

Amounts entered in the UI are dollars; the API uses integer cents. This is a single-currency model, with no rounding or exchange-rate assumptions. Receipt amounts are typed demo data, **not OCR or verified receipt evidence**. Expenses are assumed proposed eligible business costs. Refunds, personal portions, card-feed matching, grant eligibility, actual approvals, and journal entries are extension work.

## How the math works

- Total = employee-paid + corporate-card expenses.
- Every line must equal its C3 + C4 allocation; opposing differences cannot cancel each other out.
- Settlement = employee-paid expenses − applicable advances − previous reimbursements.
- Positive settlement is proposed reimbursement; negative settlement is potential employee return.
- Advances do not reduce expense or funding totals.
- Balanced means arithmetic balanced, not approved or paid.

The calculation ID fingerprints the input and rules version. This supports reproducibility, **not authentication or tamper-proof audit storage**. Downloads are local snapshots, not durable approval records.

## API / Maestro contract

Interactive API docs: http://127.0.0.1:8087/docs. `POST /api/reconcile` accepts the complete JSON document in `examples/balanced.json`:

```sh
curl -X POST http://127.0.0.1:8087/api/reconcile \
  -H 'Content-Type: application/json' \
  --data-binary @examples/balanced.json
```

Map inputs from workflow variables; map outputs such as `reimbursement_due_cents`, `allocation_summary`, `blocking_issue_count`, `ready_for_finance_review`, `issue_summary`, and `calculation_id` into branches and notifications. A 200 response can contain `needs_review`; never branch only on HTTP success. A 422 means invalid inputs, a 413 oversized content. On timeouts/errors, hold for review, never assume zero or success.

This full-payload demo differs from a future report-ID-only endpoint: that endpoint must retrieve authorized stored records. There is no database here. Array handling, response-field mapping, rich email formatting and participant binding must be tested against your Maestro account. Native invitations should supply native participant action links; do not invent approval links.

**Maestro cannot reach your work machine's localhost.** Local testing needs no deployment. To connect real Maestro later, deploy behind an approved HTTPS gateway with dedicated machine authentication, report-level authorization, rate limits, durable audit records, reviewed secret storage and outbound controls. The included server has no authentication and must not be exposed as-is. Do not change its bind address or disable trusted-host checks to work around this.

## Project layout / extension points

- `app/core.py`: pure calculation and validation; no network or disk writes.
- `app/main.py`: API, bounded request body, trusted hosts and security headers.
- `app/static/`: responsive interface, official brand assets, notification preview.
- `examples/balanced.json`: reproducible fixture.
- `tests/`: financial invariants, invalid inputs and API boundaries.

Next extensions, in order: persisted report revisions → authorized reviewer identities → expense-line/grant allocations → card-feed matching → approval events → idempotent accounting export. Keep payment execution separate. A real entity allocation requires legal entity IDs, funding codes and evidence, not just C3/C4 labels. Never let a traveler select an arbitrary approver or declare a payment confirmed.

## Test

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

GitHub Actions runs this on Python 3.10 and 3.12. Pinned dependencies provide reproducibility, not a security attestation; review/update them before production.

## Get this example from GitHub

This example lives inside the existing PUG repository. Do not initialize a nested repository.

```sh
git clone --branch examples/leadership-expense-demo https://github.com/toms-iam-demos/python-unified-gateway.git
cd python-unified-gateway/examples/leadership-expense-demo
```

Then follow the macOS/Linux or Windows setup above. If already cloned, fetch and check out the example branch first. Repository access may be required. The rest of the gateway does not need to run; this example has its own dependencies and synthetic fixtures.

Do not commit real receipts, personal data, tokens, downloaded real reports or virtual environments.

## Branding and research

Official assets sourced September 22, 2026 from https://civilrights.org/edfund/:

- `wordmark.svg`: original inline full Education Fund logo; original blue/red/gray fills from the site's stylesheet.
- `mark.png`: https://civilrights.org/edfund/wp-content/uploads/sites/2/2019/01/cropped-favicon-192x192.png

Logos and names retain their owners' rights. No endorsement or broad redistribution license is implied. Obtain brand-owner approval before public distribution. Use replacement assets if required. Application source is provided as an editable example; no third-party logo license is granted.

Organizational context: https://civilrights.org/terms-conditions/ and https://civilrights.org/about/careers/controller-finance/. Public sources do not establish internal travel policy. All dollar amounts, thresholds and scenario allocations are illustrative. This example neither determines tax compliance nor authorizes grants or payments.

The small icon uses a purple circular UI badge around the verified arc asset. It is not a claimed reproduction of a separate official purple logo. Replace `app/static/mark.png` with your approved circular asset when available.
