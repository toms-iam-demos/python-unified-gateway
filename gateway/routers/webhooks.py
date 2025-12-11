from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import asyncio
import json

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# In-memory buffer of webhook events (per process)
_webhook_events: List[Dict[str, Any]] = []
_subscribers: List[asyncio.Queue] = []


async def _broadcast_event(event: Dict[str, Any]) -> None:
    """Push an event to all connected monitor clients."""
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
    """
    Receive DocuSign Connect notifications.
    Store them for monitoring and return a simple response.
    """
    raw_body = await request.body()
    headers = dict(request.headers)

    try:
        parsed = json.loads(raw_body)
    except Exception:
        parsed = None

    event = {
        "id": len(_webhook_events) + 1,
        "source": "docusign",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "headers": headers,
        "body_raw": raw_body.decode(errors="replace"),
        "json": parsed,
    }

    _webhook_events.append(event)
    if len(_webhook_events) > 200:
        _webhook_events.pop(0)

    await _broadcast_event(event)

    return {"status": "received", "length": len(raw_body)}


@router.get("/monitor")
async def monitor_webhooks(limit: int = 50):
    """
    Simple JSON monitor of recent webhook events.
    GET /webhooks/monitor?limit=20
    """
    recent = _webhook_events[-limit:]
    return {
        "count": len(_webhook_events),
        "returned": len(recent),
        "events": recent,
    }


@router.get("/monitor/stream")
async def monitor_stream():
    """
    Server-Sent Events stream for live monitoring.
    GET /webhooks/monitor/stream
    """
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.append(queue)

    async def event_gen():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except asyncio.CancelledError:
            # client disconnected
            pass

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get("/monitor/ui", response_class=HTMLResponse)
async def monitor_ui():
    """
    Pretty dashboard similar to webhook.site, but minimal.
    GET /webhooks/monitor/ui
    """
    return HTMLResponse(MONITOR_HTML)


MONITOR_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>tifirmo.io – Webhook Monitor</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { background-color: #020617; }
    pre { white-space: pre-wrap; word-wrap: break-word; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100">
  <div class="min-h-screen flex flex-col">
    <!-- Header -->
    <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
      <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-xl bg-indigo-500 flex items-center justify-center">
            <span class="font-bold text-white text-lg">t</span>
          </div>
          <div>
            <div class="font-semibold text-sm sm:text-base">Webhook Monitor</div>
            <div class="text-xs text-slate-400">ds-gw · /webhooks/docusign</div>
          </div>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <span id="status-dot" class="h-2.5 w-2.5 rounded-full bg-yellow-400"></span>
          <span id="status-text" class="text-slate-300">Connecting…</span>
        </div>
      </div>
    </header>

    <!-- Main -->
    <main class="flex-1">
      <div class="max-w-6xl mx-auto px-4 py-4 grid grid-cols-1 md:grid-cols-[260px_minmax(0,1fr)] gap-4">
        <!-- Sidebar -->
        <aside class="space-y-4">
          <section class="bg-slate-900/60 border border-slate-800 rounded-2xl p-4">
            <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-3">
              Filters
            </h2>
            <div class="space-y-3 text-xs">
              <div>
                <div class="text-slate-400 mb-1">Status</div>
                <div class="flex flex-wrap gap-1.5">
                  <button data-status-filter="all"
                    class="status-filter px-2.5 py-1 rounded-full text-xs bg-slate-800 text-slate-100 border border-slate-700">
                    All
                  </button>
                  <button data-status-filter="ok"
                    class="status-filter px-2.5 py-1 rounded-full text-xs bg-emerald-900/40 text-emerald-300 border border-emerald-700/60">
                    OK
                  </button>
                  <button data-status-filter="warn"
                    class="status-filter px-2.5 py-1 rounded-full text-xs bg-amber-900/40 text-amber-300 border border-amber-700/60">
                    Warn
                  </button>
                  <button data-status-filter="error"
                    class="status-filter px-2.5 py-1 rounded-full text-xs bg-rose-900/40 text-rose-300 border border-rose-700/60">
                    Error
                  </button>
                </div>
              </div>

              <div>
                <div class="text-slate-400 mb-1">Search</div>
                <input id="search-input" type="text"
                  placeholder="Envelope ID, email, status…"
                  class="w-full bg-slate-950/60 border border-slate-800 rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 placeholder:text-slate-500">
              </div>

              <p class="text-[10px] text-slate-500 leading-snug">
                This view is read-only. Use it to inspect DocuSign webhook
                payloads and prototype rules/triggers.
              </p>
            </div>
          </section>
        </aside>

        <!-- Events -->
        <section class="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col min-h-[60vh]">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Live events
            </h2>
            <div class="text-[10px] text-slate-500">
              Newest first · streaming via SSE
            </div>
          </div>

          <div id="events" class="space-y-2 overflow-y-auto text-xs pr-1">
          </div>
        </section>
      </div>
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

    function statusColors(status) {
      switch (status) {
        case "ok": return "bg-emerald-900/40 border-emerald-700/60 text-emerald-200";
        case "warn": return "bg-amber-900/40 border-amber-700/60 text-amber-200";
        case "error": return "bg-rose-900/40 border-rose-700/60 text-rose-200";
        default: return "bg-slate-800/80 border-slate-700 text-slate-200";
      }
    }

    function passesFilters(evt) {
      if (activeStatusFilter !== "all" && evt.status !== activeStatusFilter) return false;
      if (!searchQuery) return true;
      const haystack = JSON.stringify(evt).toLowerCase();
      return haystack.includes(searchQuery);
    }

    function applyFilters() {
      const cards = eventsEl.querySelectorAll(".event-card");
      cards.forEach(card => {
        const status = card.dataset.status;
        const raw = card.dataset.raw || "";
        let visible = true;

        if (activeStatusFilter !== "all" && status !== activeStatusFilter) visible = false;
        if (visible && searchQuery && !raw.includes(searchQuery)) visible = false;

        card.style.display = visible ? "block" : "none";
      });
    }

    function addEvent(evt) {
      const container = document.createElement("article");
      container.className = "event-card border border-slate-800 bg-slate-950/70 rounded-xl p-3 flex flex-col gap-2";
      container.dataset.status = evt.status || "ok";
      container.dataset.raw = JSON.stringify(evt).toLowerCase();

      const header = document.createElement("div");
      header.className = "flex items-center justify-between gap-2";

      const left = document.createElement("div");
      left.className = "flex items-center gap-2";

      const badge = document.createElement("div");
      badge.className = "inline-flex items-center px-1.5 py-0.5 rounded-full border text-[10px] " + statusColors(evt.status);
      badge.textContent = (evt.status || "ok").toUpperCase();

      const title = document.createElement("div");
      title.className = "text-[11px] text-slate-200";
      const envelopeId =
        evt.json?.envelopeId ||
        evt.json?.EnvelopeID ||
        evt.json?.EnvelopeId ||
        "Envelope";
      title.textContent = envelopeId;

      left.appendChild(badge);
      left.appendChild(title);

      const right = document.createElement("div");
      right.className = "flex items-center gap-2 text-[10px] text-slate-500";

      const ts = document.createElement("span");
      ts.textContent = new Date(evt.timestamp || Date.now()).toLocaleString();
      right.appendChild(ts);

      header.appendChild(left);
      header.appendChild(right);

      const body = document.createElement("div");
      body.className = "bg-slate-950/80 border border-slate-800 rounded-lg p-2 text-[10px] text-slate-200 font-mono";

      const pre = document.createElement("pre");
      pre.textContent = evt.json ? JSON.stringify(evt.json, null, 2) : (evt.body_raw || "");
      body.appendChild(pre);

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
        statusButtons.forEach(b => b.classList.remove("ring-1", "ring-indigo-500"));
        btn.classList.add("ring-1", "ring-indigo-500");
        applyFilters();
      });
    });

    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value.trim().toLowerCase();
      applyFilters();
    });

    function connect() {
      const es = new EventSource("/webhooks/monitor/stream");

      es.onopen = () => {
        statusDot.className = "h-2.5 w-2.5 rounded-full bg-emerald-400";
        statusText.textContent = "Connected";
      };

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          addEvent(data);
        } catch (e) {
          console.error("Bad event", e);
        }
      };

      es.onerror = () => {
        statusDot.className = "h-2.5 w-2.5 rounded-full bg-rose-400";
        statusText.textContent = "Disconnected – retrying…";
        es.close();
        setTimeout(connect, 3000);
      };
    }

    connect();
  </script>
</body>
</html>
"""