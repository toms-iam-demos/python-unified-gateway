# Portable PUG examples

| Example | Start | What it proves |
| --- | --- | --- |
| [Leadership expense reconciliation](leadership-expense-demo/README.md) | `python run.py` after installing dependencies. Port 8087. | Receipt arithmetic, C3/C4 allocations, reimbursement and advance reconciliation. No payments or provider calls. |
| [Houston procurement intelligence](houston-procurement-demo/README.md) | `python run.py` inside its folder, after installing dependencies | Four Houston-informed review scenarios, 10,000 synthetic records, evidence gates, receipt recovery, source register and technical report. Port 8089. No provider connection. |
| [Getty procurement playground](getty-procurement-demo/README.md) | `python run.py` inside its folder, after installing dependencies | Local stateful simulation: procurement plans, approval walkthrough, arithmetic, replay protection and recovery. No provider connection. |

Each example runs in its own virtual environment and port. The Getty example defaults to 8088 so it can run alongside the Education Fund expense demo on 8087. Examples do not automatically become deployed gateway routes.

All three packages are included together on this collection branch. Local experiments remain under Git-ignored `local-dev/`; runtime data and secrets must not be committed.

See [security review](SECURITY-REVIEW.md) for tested boundaries and remaining limitations.

## Download once, run any demo

Use Python 3.11 or 3.14 (the versions exercised in CI). Install Git only if using the clone option. No PUG server, docusign credentials, Docker, Node or Java is needed to run these examples. Installation needs access to Python package downloads. Optional Swagger documentation uses hosted assets.

**Option A — Git:** use a new destination folder to preserve any existing checkout:

```sh
git clone --single-branch --branch examples/reviewed-demo-collection https://github.com/toms-iam-demos/python-unified-gateway.git pug-demo-collection
cd pug-demo-collection/examples/houston-procurement-demo
```

**Option B — no Git:** [download this branch as a ZIP](https://github.com/toms-iam-demos/python-unified-gateway/archive/refs/heads/examples/reviewed-demo-collection.zip), extract it fully, then open a terminal inside `examples/houston-procurement-demo` in the extracted folder. The default main-branch download does not yet contain this reviewed collection.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Use `py -3.14` instead if that is the installed tested version. Calling the virtual environment's Python directly avoids PowerShell activation-policy changes.

### macOS or Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
```

Open http://127.0.0.1:8089 for Houston. To run Getty or expense instead, enter its sibling folder and repeat setup there: Getty uses 8088; expense uses 8087. Each demo gets its own virtual environment. All three can run together in separate terminals.

Stop with Ctrl+C. Restart with the final command. To choose a free port, append `--port 8090`. Procurement records persist in each example's ignored `data/` directory; the expense calculation is stateless. Use the in-app reset workflow for procurement data. Never copy `.venv` between machines; recreate it. Transfer the entire example folder, including static assets and fixtures, not just `run.py`.

### Updating later

In a clean Git checkout of this branch, run `git pull --ff-only`, then rerun the dependency-install command in each example you use and restart it. ZIP users download a fresh copy into a new folder; generated records are not included. Do not overwrite an installation containing local changes or data.

The collection workflow runs each example's tests independently on Windows and Linux with both tested Python versions. CI does not require gateway credentials or reach provider APIs.
