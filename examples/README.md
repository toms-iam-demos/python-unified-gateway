# Portable PUG examples

| Example | Start | What it proves |
| --- | --- | --- |
| [Leadership expense reconciliation](leadership-expense-demo/README.md) | `python run.py` after installing dependencies. Port 8087. | Receipt arithmetic, C3/C4 allocations, reimbursement and advance reconciliation. No payments or provider calls. |
| [Houston procurement intelligence](houston-procurement-demo/README.md) | `python run.py` inside its folder, after installing dependencies | Four Houston-informed review scenarios, 10,000 synthetic records, evidence gates, receipt recovery, source register and technical report. Port 8089. No provider connection. |
| [Getty procurement playground](getty-procurement-demo/README.md) | `python run.py` inside its folder, after installing dependencies | Local stateful simulation: procurement plans, approval walkthrough, arithmetic, replay protection and recovery. No provider connection. |

Each example runs in its own virtual environment and port. The Getty example defaults to 8088 so it can run alongside the Education Fund expense demo on 8087. Examples do not automatically become deployed gateway routes.

All three packages are included together on this collection branch. Local experiments remain under Git-ignored `local-dev/`; runtime data and secrets must not be committed.

See [security review](SECURITY-REVIEW.md) for tested boundaries and remaining limitations.
