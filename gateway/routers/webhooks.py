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


MONITOR_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>tifirmo.io – Webhook Console</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <!-- Collapsible, colored JSON renderer (optional but nice) -->
  <script src="https://cdn.jsdelivr.net/npm/renderjson@1.4.0/renderjson.min.js"></script>

  <style>
    :root{
      --bg:#020617;
      --panel: rgba(15,23,42,.72);
      --panel2: rgba(2,6,23,.55);
      --border: rgba(148,163,184,.18);
      --text:#e2e8f0;
      --muted:#94a3b8;
      --muted2:#64748b;
      --brand:#6366f1; /* indigo */
      --ok:#34d399;
      --warn:#fbbf24;
      --err:#fb7185;
      --shadow: 0 18px 60px rgba(0,0,0,.45);
      --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono","Courier New", monospace;
      --sans: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
    }

    *{ box-sizing:border-box; }
    html, body{ height:100%; }
    body{
      margin:0;
      background: radial-gradient(1200px 800px at 20% 0%, rgba(99,102,241,.16), transparent 60%),
                  radial-gradient(900px 700px at 90% 10%, rgba(34,211,238,.10), transparent 55%),
                  var(--bg);
      color:var(--text);
      font-family: var(--sans);
    }

    .wrap{ min-height:100%; display:flex; flex-direction:column; }
    .topbar{
      position:sticky; top:0;
      backdrop-filter: blur(10px);
      background: rgba(2,6,23,.72);
      border-bottom: 1px solid var(--border);
      z-index:10;
    }
    .topbar-inner{
      max-width: 1100px;
      margin: 0 auto;
      padding: 14px 18px;
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:14px;
    }

    .brand{
      display:flex; align-items:center; gap:12px; min-width:0;
    }
    .logo{
      width:36px; height:36px;
      border-radius: 14px;
      background: linear-gradient(135deg, rgba(99,102,241,1), rgba(79,70,229,1));
      box-shadow: 0 10px 30px rgba(99,102,241,.25);
      display:flex; align-items:center; justify-content:center;
      flex:0 0 auto;
    }
    .logo span{ font-weight: 800; font-size:18px; color:white; letter-spacing:.5px; }
    .title{ display:flex; flex-direction:column; min-width:0; }
    .title h1{ margin:0; font-size:14px; font-weight: 700; letter-spacing:.2px; }
    .title .sub{ font-size:12px; color: var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

    .status{
      display:flex; align-items:center; gap:10px;
      font-size:12px; color: var(--muted);
      flex: 0 0 auto;
    }
    .dot{
      width:10px; height:10px; border-radius:50%;
      background: var(--warn);
      box-shadow: 0 0 0 4px rgba(251,191,36,.14);
    }

    .main{
      flex:1;
      max-width:1100px;
      margin: 0 auto;
      padding: 18px;
      display:grid;
      grid-template-columns: 280px minmax(0,1fr);
      gap:16px;
    }

    .card{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: var(--shadow);
      overflow:hidden;
    }
    .card-h{
      padding: 14px 14px 10px 14px;
      border-bottom: 1px solid var(--border);
      display:flex; align-items:center; justify-content:space-between; gap:10px;
    }
    .card-h .k{ font-size:11px; letter-spacing:.12em; color: var(--muted); font-weight:700; text-transform:uppercase; }
    .card-b{ padding: 14px; }

    .btn-row{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
    .btn{
      appearance:none;
      border:1px solid var(--border);
      background: rgba(30,41,59,.55);
      color: var(--text);
      font-size:12px;
      padding:6px 10px;
      border-radius: 999px;
      cursor:pointer;
      transition: transform .06s ease, background .12s ease, border-color .12s ease;
    }
    .btn:hover{ background: rgba(30,41,59,.85); }
    .btn:active{ transform: translateY(1px); }
    .btn.active{ border-color: rgba(99,102,241,.65); box-shadow: 0 0 0 3px rgba(99,102,241,.14); }

    .btn.ok{ color: #c7f9e9; background: rgba(16,185,129,.12); border-color: rgba(16,185,129,.35); }
    .btn.warn{ color: #fff1c2; background: rgba(245,158,11,.12); border-color: rgba(245,158,11,.35); }
    .btn.err{ color: #ffd3dc; background: rgba(244,63,94,.10); border-color: rgba(244,63,94,.30); }

    .input{
      width:100%;
      border:1px solid var(--border);
      background: rgba(2,6,23,.6);
      color: var(--text);
      padding: 10px 11px;
      border-radius: 12px;
      font-size: 12px;
      outline: none;
    }
    .input:focus{
      border-color: rgba(99,102,241,.6);
      box-shadow: 0 0 0 3px rgba(99,102,241,.16);
    }

    .events{
      display:flex; flex-direction:column; gap:10px;
      max-height: calc(100vh - 180px);
      overflow:auto;
      padding-right: 4px;
    }
    .evt{
      border:1px solid var(--border);
      background: rgba(2,6,23,.55);
      border-radius: 14px;
      padding: 12px;
      display:flex; flex-direction:column; gap:10px;
    }
    .evt-h{
      display:flex; align-items:center; justify-content:space-between; gap:10px;
    }
    .badge{
      font-size: 10px;
      letter-spacing:.08em;
      font-weight: 800;
      padding: 3px 8px;
      border-radius: 999px;
      border:1px solid var(--border);
      background: rgba(30,41,59,.6);
      color: var(--text);
      text-transform: uppercase;
      flex: 0 0 auto;
    }
    .badge.ok{ border-color: rgba(16,185,129,.35); background: rgba(16,185,129,.10); color: #c7f9e9; }
    .badge.warn{ border-color: rgba(245,158,11,.35); background: rgba(245,158,11,.10); color: #fff1c2; }
    .badge.err{ border-color: rgba(244,63,94,.30); background: rgba(244,63,94,.08); color: #ffd3dc; }

    .evt-title{
      font-size: 12px;
      color: var(--text);
      white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
      font-weight: 650;
    }
    .evt-ts{
      font-size: 11px;
      color: var(--muted2);
      flex: 0 0 auto;
    }
    .evt-body{
      border:1px solid var(--border);
      background: rgba(2,6,23,.7);
      border-radius: 12px;
      padding: 10px;
      font-family: var(--mono);
      font-size: 11px;
      overflow:auto;
      max-height: 360px;
    }
    pre{ margin:0; white-space: pre-wrap; word-wrap: break-word; }

    /* renderjson palette */
    .renderjson a { text-decoration:none; }
    .renderjson .disclosure { color: #a5b4fc; }
    .renderjson .syntax { color: #94a3b8; }
    .renderjson .string { color: #34d399; }
    .renderjson .number { color: #60a5fa; }
    .renderjson .boolean { color: #fbbf24; }
    .renderjson .null { color: #fb7185; }
    .renderjson .key { color: #e2e8f0; }

    @media (max-width: 900px){
      .main{ grid-template-columns: 1fr; }
      .events{ max-height: none; }
    }
  </style>
</head>

<body>
  <div class="wrap">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <div class="logo"><span>t</span></div>
          <div class="title">
            <h1>Webhook Console</h1>
            <div class="sub">/webhooks/docusign · live via SSE</div>
          </div>
        </div>
        <div class="status">
          <span id="status-dot" class="dot"></span>
          <span id="status-text">Connecting…</span>
        </div>
      </div>
    </header>

    <main class="main">
      <section class="card">
        <div class="card-h">
          <div class="k">Filters</div>
        </div>
        <div class="card-b">
          <div style="font-size:12px; color: var(--muted); margin-bottom:8px;">Status</div>
          <div class="btn-row">
            <button data-status-filter="all" class="btn status-filter active">All</button>
            <button data-status-filter="ok" class="btn status-filter ok">OK</button>
            <button data-status-filter="warn" class="btn status-filter warn">Warn</button>
            <button data-status-filter="error" class="btn status-filter err">Error</button>
          </div>

          <div style="height:12px;"></div>

          <div style="font-size:12px; color: var(--muted); margin-bottom:8px;">Search</div>
          <input id="search-input" class="input" type="text" placeholder="Envelope ID, email, status…" />

          <div style="height:12px;"></div>
          <div style="font-size:11px; color: var(--muted2); line-height:1.35;">
            Read-only. Use this to inspect inbound payloads and prototype rules/triggers.
          </div>
        </div>
      </section>

      <section class="card">
        <div class="card-h">
          <div class="k">Live events</div>
          <div style="font-size:11px; color: var(--muted2);">newest first</div>
        </div>
        <div class="card-b">
          <div id="events" class="events"></div>
        </div>
      </section>
    </main>
  </div>

  <script>
    const statusDot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");
    const eventsEl = document.getElementById("events");
    const searchInput = document.getElementById("search-input");
    const statusButtons = document.querySelectorAll(".status-filter");

    let activeStatusFilter = "all";
    let searchQuery = "";

    function badgeClass(status) {
      switch ((status || "").toLowerCase()) {
        case "ok": return "badge ok";
        case "warn": return "badge warn";
        case "error": return "badge err";
        default: return "badge";
      }
    }

    function applyFilters() {
      const cards = eventsEl.querySelectorAll(".evt");
      cards.forEach(card => {
        const status = card.dataset.status;
        const raw = card.dataset.raw || "";
        let visible = true;

        if (activeStatusFilter !== "all" && status !== activeStatusFilter) visible = false;
        if (visible && searchQuery && !raw.includes(searchQuery)) visible = false;

        card.style.display = visible ? "flex" : "none";
      });
    }

    function envelopeIdFor(evt) {
      return (
        evt?.json?.envelopeId ||
        evt?.json?.EnvelopeID ||
        evt?.json?.EnvelopeId ||
        "Envelope"
      );
    }

    function addEvent(evt) {
      const container = document.createElement("article");
      container.className = "evt";
      container.dataset.status = (evt.status || "ok").toLowerCase();
      container.dataset.raw = JSON.stringify(evt).toLowerCase();

      const header = document.createElement("div");
      header.className = "evt-h";

      const left = document.createElement("div");
      left.style.display = "flex";
      left.style.alignItems = "center";
      left.style.gap = "10px";
      left.style.minWidth = "0";

      const badge = document.createElement("div");
      badge.className = badgeClass(evt.status);
      badge.textContent = (evt.status || "ok").toUpperCase();

      const title = document.createElement("div");
      title.className = "evt-title";
      title.textContent = envelopeIdFor(evt);

      left.appendChild(badge);
      left.appendChild(title);

      const ts = document.createElement("div");
      ts.className = "evt-ts";
      ts.textContent = new Date(evt.timestamp || Date.now()).toLocaleString();

      header.appendChild(left);
      header.appendChild(ts);

      const body = document.createElement("div");
      body.className = "evt-body";

      // Prefer renderjson (collapsible) if present; fall back to <pre>.
      if (evt.json && typeof renderjson === "function") {
        renderjson.set_show_to_level(2);
        renderjson.set_icons("▶", "▼");
        const tree = renderjson(evt.json);
        tree.className = "renderjson";
        body.appendChild(tree);
      } else {
        const pre = document.createElement("pre");
        pre.textContent = evt.json ? JSON.stringify(evt.json, null, 2) : (evt.body_raw || "");
        body.appendChild(pre);
      }

      container.appendChild(header);
      container.appendChild(body);

      eventsEl.insertBefore(container, eventsEl.firstChild);

      while (eventsEl.childNodes.length > 200) {
        eventsEl.removeChild(eventsEl.lastChild);
      }

      applyFilters();
    }

    statusButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        activeStatusFilter = btn.dataset.statusFilter;

        statusButtons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

        applyFilters();
      });
    });

    searchInput.addEventListener("input", (e) => {
      searchQuery = (e.target.value || "").trim().toLowerCase();
      applyFilters();
    });

    function connect() {
      const es = new EventSource("/webhooks/monitor/stream");

      es.onopen = () => {
        statusDot.style.background = "var(--ok)";
        statusDot.style.boxShadow = "0 0 0 4px rgba(52,211,153,.14)";
        statusText.textContent = "Connected";
      };

      es.onmessage = (event) => {
        try { addEvent(JSON.parse(event.data)); } catch (e) { console.error(e); }
      };

      es.onerror = () => {
        statusDot.style.background = "var(--err)";
        statusDot.style.boxShadow = "0 0 0 4px rgba(251,113,133,.14)";
        statusText.textContent = "Disconnected – retrying…";
        es.close();
        setTimeout(connect, 1500);
      };
    }

    connect();
  </script>
</body>
</html>
"""
