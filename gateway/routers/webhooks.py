from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import asyncio
import functools
import json
import logging
import os

import anyio

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from gateway.db.events_store import persist_inbound_event
from gateway.connect_hmac import require_connect_hmac
from gateway.observability import span, current

log = logging.getLogger(__name__)

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


DEFAULT_MAX_BODY_BYTES = 16 * 1024 * 1024


def max_body_bytes() -> int:
    """Upper bound on an unauthenticated request body, read before HMAC."""
    value = os.getenv("DOCUSIGN_CONNECT_MAX_BODY_BYTES", "").strip()
    try:
        limit = int(value)
    except ValueError:
        return DEFAULT_MAX_BODY_BYTES
    return limit if limit > 0 else DEFAULT_MAX_BODY_BYTES


class BodyTooLarge(Exception):
    pass


async def read_bounded_body(request: Request, limit: int) -> bytes:
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            if int(declared) > limit:
                raise BodyTooLarge()
        except ValueError:
            pass  # Malformed lengths are bounded by the streaming read below.
    chunks: List[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > limit:
            raise BodyTooLarge()
        chunks.append(chunk)
    return b"".join(chunks)


def dedupe_basis(parsed: Any) -> bytes | None:
    """Connect increments top-level retryCount on redelivery; exclude only that field.

    Returns None (raw-body deduplication) for anything else, so payloads without
    retryCount keep their existing ledger keys.
    """
    if not isinstance(parsed, dict) or "retryCount" not in parsed:
        return None
    semantic = {k: v for k, v in parsed.items() if k != "retryCount"}
    return json.dumps(semantic, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@router.post("/docusign")
async def docusign_webhook(request: Request):
    try:
        raw_body = await read_bounded_body(request, max_body_bytes())
    except BodyTooLarge:
        log.warning("connect_webhook_rejected reason=body_too_large")
        return JSONResponse({"detail": "Webhook body too large"}, status_code=413)
    with span("webhook HMAC verification"):
        require_connect_hmac(raw_body, request.headers.items())
    headers = dict(request.headers)

    try:
        parsed = json.loads(raw_body)
    except Exception:
        parsed = None

    # Custody (ADR-0002): a verified event that is not durably recorded is
    # answered with 503 so Connect redelivers it. Offloaded to a worker thread:
    # sqlite3 is synchronous, and running it inline on this coroutine would
    # block the event loop for every other in-flight request on this worker
    # for the duration of the disk write. Verification still happens before
    # persistence as required by ADR-0010. Correlation IDs are server-assigned
    # (ADR-0009); client headers remain visible only in headers_json.
    with span("webhook idempotency / ledger persistence"):
        persist_result = await anyio.to_thread.run_sync(
            functools.partial(
                persist_inbound_event,
                source="docusign",
                method=request.method,
                host=headers.get("host", ""),
                path=str(request.url.path),
                remote_addr=request.client.host if request.client else None,
                headers=headers,
                raw_body=raw_body,
                json_parsed=parsed if isinstance(parsed, dict) else None,
                verify_status="verified",
                verify_reason="hmac-sha256",
                dedupe_basis=dedupe_basis(parsed),
            )
        )
    persisted = bool(persist_result.get("persisted"))
    # Only an explicitly disabled ledger (GATEWAY_DB_ENABLED=0) may acknowledge
    # without a receipt; any other failure asks the provider to redeliver.
    retry_required = not persisted and persist_result.get("db_mode") != "disabled"
    if retry_required:
        log.warning("Verified Docusign webhook not persisted; returning 503 for redelivery.")
    elif not persisted:
        log.warning("Verified Docusign webhook acknowledged without a ledger receipt.")
    trace = current.get()
    if trace is not None:
        trace["event_id"] = persist_result.get("event_id")
        trace["persisted"] = persisted


    monitor_persistence = persist_result
    if persist_result.get("db_mode") == "degraded":
        monitor_persistence = {**persist_result, "db_detail": "database unavailable"}

    event = {
        "id": len(_webhook_events) + 1,
        "source": "docusign",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "headers": headers,
        "body_raw": raw_body.decode(errors="replace"),
        "json": parsed,
        "persistence": monitor_persistence,
        "status": "ok" if persisted else "warn",
    }

    _webhook_events.append(event)
    if len(_webhook_events) > 200:
        _webhook_events.pop(0)

    await _broadcast_event(event)

    if retry_required:
        return JSONResponse(
            {"status": "retry", "length": len(raw_body), "persisted": False},
            status_code=503,
            headers={"Retry-After": "60"},
        )
    return {
        "status": "received",
        "length": len(raw_body),
        "persisted": persisted,
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
