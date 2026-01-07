from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from gateway.db.events_store import persist_inbound_event

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# In-memory buffer of webhook events (per process)
_webhook_events: List[Dict[str, Any]] = []
_subscribers: List[asyncio.Queue] = []


async def _broadcast_event(event: Dict[str, Any]) -> None:
    dead: List[asyncio.Queue] = []
    for q in _subscribers:
        try:
            await q.put(event)
        except Exception:
            dead.append(q)
    for q in dead:
        if q in _subscribers:
            _subscribers.remove(q)


@router.post("/docusign")
async def docusign_webhook(request: Request):
    raw_body = await request.body()
    headers = dict(request.headers)

    try:
        parsed = json.loads(raw_body)
    except Exception:
        parsed = None

    # Best-effort persistence (fail-open)
    persist_result = persist_inbound_event(
        source="docusign",
        method=request.method,
        host=headers.get("host", ""),
        path=str(request.url.path),
        remote_addr=request.client.host if request.client else None,
        headers=headers,
        raw_body=raw_body,
        json_parsed=parsed if isinstance(parsed, dict) else None,
        correlation_id=headers.get("x-correlation-id") or headers.get("x-request-id"),
    )

    event = {
        "id": len(_webhook_events) + 1,
        "source": "docusign",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "headers": headers,
        "body_raw": raw_body.decode(errors="replace"),
        "json": parsed,
        "persistence": persist_result,
        "status": "ok" if persist_result.get("persisted") else "warn",
    }

    _webhook_events.append(event)
    if len(_webhook_events) > 200:
        _webhook_events.pop(0)

    await _broadcast_event(event)

    return {
        "status": "received",
        "length": len(raw_body),
        "persisted": bool(persist_result.get("persisted")),
    }


@router.get("/monitor")
async def monitor_webhooks(limit: int = 50):
    recent = _webhook_events[-limit:]
    return {"count": len(_webhook_events), "returned": len(recent), "events": recent}


@router.get("/monitor/stream")
async def monitor_stream():
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.append(queue)

    async def event_gen():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get("/monitor/ui", response_class=HTMLResponse)
async def monitor_ui():
    return HTMLResponse(MONITOR_HTML)


MONITOR_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>PUG – Webhook Monitor</title>
  <style>
    :root {
      --ok: #34d399;
      --warn: #facc15;
      --bad: #ef4444;
      --bg: #0b1020;
      --panel: #11162a;
      --ink: #e6edf3;
      --muted: #9aa4b2;
      --line: #1f2937;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
      background: var(--bg);
      color: var(--ink);
    }
    header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 14px;
      border-bottom: 1px solid var(--line);
      background: #0e1430;
    }
    header strong { letter-spacing: .2px; }
    .pill {
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--muted);
    }
    .ok   { background: rgba(52,211,153,.12); color:#b7f3d1; border-color:#1f5f4a; }
    .warn { background: rgba(250,204,21,.12); color:#fde68a; border-color:#6b5a16; }
    .bad  { background: rgba(239,68,68,.12); color:#fecaca; border-color:#6b1b1b; }

    main {
      display: grid;
      grid-template-columns: 420px 1fr;
      height: calc(100vh - 50px);
    }
    #left {
      border-right: 1px solid var(--line);
      overflow: auto;
      background: #0e1430;
    }
    #right {
      overflow: auto;
      padding: 14px;
    }
    ul { list-style: none; margin: 0; padding: 0; }
    li {
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      cursor: pointer;
    }
    li:hover { background: #0f1738; }
    .meta {
      font-size: 11px;
      color: var(--muted);
      display: flex;
      justify-content: space-between;
      gap: 10px;
    }
    .title {
      font-weight: 600;
      margin: 6px 0;
      word-break: break-all;
    }
    pre {
      background: #020617;
      border: 1px solid var(--line);
      padding: 12px;
      border-radius: 10px;
      overflow: auto;
      color: var(--ink);
    }
    .row { display: flex; gap: 10px; flex-wrap: wrap; }
    button {
      padding: 6px 10px;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: #0f1738;
      color: var(--ink);
      cursor: pointer;
    }
    button:hover { background: #111c44; }
  </style>
</head>
<body>

<header>
  <strong>Webhook Monitor</strong>
  <span id="status" class="pill warn">Initializing…</span>
  <span class="pill">Mode: <code id="mode">init</code></span>
  <span class="pill">Source: <code id="src">any</code></span>
  <div style="margin-left:auto" class="row">
    <button id="refresh">Refresh</button>
    <button id="clear">Clear UI</button>
  </div>
</header>

<main>
  <section id="left">
    <ul id="list"></ul>
  </section>

  <section id="right">
    <div class="row">
      <span class="pill">Selected: <code id="sel">none</code></span>
    </div>

    <h3>Parsed JSON</h3>
    <pre id="json">{}</pre>

    <h3>Headers</h3>
    <pre id="headers">{}</pre>

    <h3>Raw body</h3>
    <pre id="raw"></pre>
  </section>
</main>


<script src="/static/monitor.js?v=4"></script>


</body>
</html>
"""
