# Portable PUG examples

| Example | Start | What it proves |
| --- | --- | --- |
| [Houston procurement intelligence](houston-procurement-demo/README.md) | `python run.py` inside its folder, after installing dependencies | Four Houston-informed review scenarios, 10,000 synthetic records, evidence gates, receipt recovery, source register and technical report. Port 8089. No provider connection. |
| [Getty procurement playground](getty-procurement-demo/README.md) | `python run.py` inside its folder, after installing dependencies | Local stateful simulation: procurement plans, approval walkthrough, arithmetic, replay protection and recovery. No provider connection. |

Each example runs in its own virtual environment and port. The Getty example defaults to 8088 so it can run alongside the Education Fund expense demo on 8087. Examples do not automatically become deployed gateway routes.

The expense demo is also available on the `examples/leadership-expense-demo` branch until its separate publication is merged. Local experiments remain under Git-ignored `local-dev/`; runtime data and secrets must not be committed.
