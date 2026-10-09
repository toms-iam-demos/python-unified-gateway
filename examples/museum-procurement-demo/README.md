# Museum procurement playground · PUG

A portable FastAPI site for three fictional Museum-context procurement stories: exhibition fabrication, archival digitization and conservation equipment service. Stateful local execution, not connected docusign, Oracle or OIC. No provider credentials, network adapters, payment or email operations exist.

## Start on your machine

Requires Python 3.10+ (tested on the version recorded in VERIFICATION.md).

```sh
cd examples/museum-procurement-demo
python -m venv .venv
```

Activate on macOS/Linux:

```sh
source .venv/bin/activate
```

Activate in Windows PowerShell (subject to your workplace's script policy):

```powershell
.venv\Scripts\Activate.ps1
```

Then:

```sh
python -m pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:8088/**. Stop with **Ctrl+C** in that terminal. Restart with the same command; state persists. If 8088 is occupied, use `python run.py --port 8089`. The expense demo can remain on 8087. There is no auto-start background service.

If activation is blocked, use `.venv\Scripts\python.exe` directly on Windows (or `.venv/bin/python` on macOS/Linux) for install and run commands.

## Five-minute demonstration

1. Build three records. Choose Exhibition fabrication. Prepare, approve as the **demo reviewer persona**, execute. The $150,000 commitment remains unchanged under a $180,000 ceiling.
2. Choose Archival digitization. Adjust accepted images; at 9,800 the eligible amount is $23,520 and $480 remains held. Prepare, approve and execute to record local acceptance. No invoice is paid.
3. Choose Equipment service. Select “Destination saves; response lost.” Prepare the $6,500 amendment, approve and execute. Observe `unknown`, then reconcile. Commitment becomes $54,500 exactly once.
4. Replay an executed command. The saved receipt suppresses another effect. Separately reset and run the version-conflict drill; rebuild a fresh plan after the conflict.
5. Download evidence JSON. Reset using the exact cohort confirmation shown. Seed up to 10,000 records to inspect dashboard aggregation and export; this **does not** execute 10,000 commands or make provider calls.

## Scope and controls

- Default bind is loopback only. Do not expose through the production reverse proxy or change host binding without an identity/security design.
- Host allowlist, per-process UI token and same-origin checks protect local API interactions. These are not a multi-user authentication system. Anyone who can browse the local UI can act as the demo reviewer.
- Every plan freezes its target and destination version. Sliders do not revise a saved plan. Exact local approval is required before execution.
- Unknown outcomes use a persisted command receipt and read-back, not blind resend. The normal path commits and reads local destination state within the simulator; it does not test distributed Oracle transport.
- SQLite state lives in `data/demo.db`, ignored by Git. Cohort reset preserves audit history and records belonging to other cohorts. Delete this example's `data` directory **with the server stopped** only if you intend to erase all its local history.
- One completed action per seeded PO is modeled. Subsequent rework/amendment lifecycles from the architecture guide are future increments, not hidden capabilities.
- Prices omit taxes, freight and FX. No actual Museum procurement rules, data, logo or endorsement are asserted.
- `/docs` documents proposed local operations. API calls require the browser's `X-Demo-Token`; the UI is the supported guided execution surface. This is not production PUG Swagger or a provider proxy.

## Development and portable component boundary

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

`app/main.py` holds the simulator API and persistence. `app/static/` holds the dependency-free frontend. `fixtures/` contains canonical JSON and editable PlantUML diagram sources. No Node build, CDN fonts or Java is needed to run the site. PlantUML is an optional authoring tool for those diagrams, not a runtime dependency.

This directory is a standalone PUG example. A catalog can link to its local port; importing it into the deployed gateway is deliberately not done. Promote shared domain code later only after real authentication, access controls and provider contract tests are in place. GitHub CI runs only this example's tests; no deployment job is added.

Context: synthetic museum operations; no real institution is represented.
