from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import APIRouter, Query

from gateway.db.init_db import ensure_schema
from gateway.db.sqlite import connect

router = APIRouter(prefix="/events", tags=["events"])


def _as_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert a DBStatus-like object (or dict/bool) into a plain dict.

    Supports:
      - dict
      - pydantic v2: model_dump()
      - pydantic v1: dict()
      - dataclass/objects: __dict__
      - bool
    """
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, bool):
        return {"ready": obj, "db": {"mode": "bool"}}

    md = getattr(obj, "model_dump", None)
    if callable(md):
        try:
            out = md()
            if isinstance(out, dict):
                return out
        except Exception:
            pass

    d = getattr(obj, "dict", None)
    if callable(d):
        try:
            out = d()
            if isinstance(out, dict):
                return out
        except Exception:
            pass

    try:
        out = dict(getattr(obj, "__dict__", {}))
        if out:
            return out
    except Exception:
        pass

    return {"ready": False, "db": {"mode": "unknown", "detail": str(obj)}}


def _db_status() -> Dict[str, Any]:
    """
    Call ensure_schema() safely and normalize output to:
      {"ready": bool, "db": dict}
    Never raises.
    """
    try:
        raw = ensure_schema()
        data = _as_dict(raw)
        ready = bool(data.get("ready", False))
        db = data.get("db", {})
        if not isinstance(db, dict):
            db = {"detail": str(db)}
        return {"ready": ready, "db": db}
    except Exception as e:
        return {"ready": False, "db": {"mode": "error", "detail": str(e)}}


def _truncate(s: Optional[str], max_len: int) -> Optional[str]:
    if s is None:
        return None
    if len(s) <= max_len:
        return s
    return s[:max_len] + f"...({len(s)} chars)"


def _body_to_text(body: Optional[Union[bytes, bytearray, str]], max_len: int) -> Optional[str]:
    """
    body_raw is stored as a BLOB in SQLite (bytes).
    Convert to display-safe text with truncation.
    """
    if body is None:
        return None
    if isinstance(body, (bytes, bytearray)):
        txt = bytes(body).decode("utf-8", errors="replace")
        return _truncate(txt, max_len)
    if isinstance(body, str):
        return _truncate(body, max_len)
    return _truncate(str(body), max_len)


def _fetchall_dicts(conn, sql: str, params: Tuple[Any, ...]) -> List[Dict[str, Any]]:
    """
    Return rows as list[dict] regardless of sqlite row_factory (tuple vs sqlite3.Row).
    """
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    out: List[Dict[str, Any]] = []
    for r in rows:
        if isinstance(r, dict):
            out.append(r)
        else:
            out.append(dict(zip(cols, r)))
    return out


def _fetchone_dict(conn, sql: str, params: Tuple[Any, ...]) -> Optional[Dict[str, Any]]:
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description] if cur.description else []
    r = cur.fetchone()
    if r is None:
        return None
    if isinstance(r, dict):
        return r
    return dict(zip(cols, r))


def _maybe_parse_json(text: Optional[str], include_parsed: int) -> Optional[Any]:
    """
    json_parsed is stored as TEXT. It may already be JSON or may be None.
    For safety and stability, we only attempt json.loads if requested.
    """
    if not include_parsed or not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


@router.get("/latest")
async def latest_events(
    limit: int = Query(50, ge=1, le=200),
    include_body: int = Query(0, ge=0, le=1),
    body_max_chars: int = Query(4000, ge=256, le=200000),
    include_json_obj: int = Query(0, ge=0, le=1),
) -> Dict[str, Any]:
    """
    DB-backed latest events (schema-aligned).
    Safe-by-default: body omitted unless include_body=1.
    Returns HTTP 200 even when DB is disabled/degraded.
    """
    status = _db_status()
    if not status["ready"]:
        return {"ready": False, "db": status["db"], "returned": 0, "events": []}

    sql = """
        select
          event_id,
          kind,
          source,
          namespace,
          correlation_id,
          parent_event_id,
          received_at,
          method,
          host,
          path,
          remote_addr,
          status_code,
          headers_json,
          body_sha256,
          json_parsed,
          verify_status,
          verify_reason,
          dedupe_key,
          body_raw
        from events
        order by received_at desc
        limit ?
    """

    try:
        c = connect()
        rows = _fetchall_dicts(c, sql, (limit,))
    except Exception as e:
        return {
            "ready": False,
            "db": {**status["db"], "mode": "error", "detail": str(e)},
            "returned": 0,
            "events": [],
        }
    finally:
        try:
            c.close()
        except Exception:
            pass

    events: List[Dict[str, Any]] = []
    for r in rows:
        evt = {
            "event_id": r.get("event_id"),
            "kind": r.get("kind"),
            "source": r.get("source"),
            "namespace": r.get("namespace"),
            "correlation_id": r.get("correlation_id"),
            "parent_event_id": r.get("parent_event_id"),
            "received_at": r.get("received_at"),
            "method": r.get("method"),
            "host": r.get("host"),
            "path": r.get("path"),
            "remote_addr": r.get("remote_addr"),
            "status_code": r.get("status_code"),
            "headers_json": r.get("headers_json"),
            "body_sha256": r.get("body_sha256"),
            "json_parsed": r.get("json_parsed"),
            "json_obj": _maybe_parse_json(r.get("json_parsed"), include_json_obj),
            "verify_status": r.get("verify_status"),
            "verify_reason": r.get("verify_reason"),
            "dedupe_key": r.get("dedupe_key"),
        }
        if include_body:
            evt["body_raw"] = _body_to_text(r.get("body_raw"), body_max_chars)

        events.append(evt)

    return {"ready": True, "db": status["db"], "returned": len(events), "events": events}


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    include_body: int = Query(1, ge=0, le=1),
    body_max_chars: int = Query(200000, ge=256, le=200000),
    include_json_obj: int = Query(1, ge=0, le=1),
) -> Dict[str, Any]:
    """
    Fetch a single event by event_id.
    Returns HTTP 200 with event=None if not found.
    Never crashes if DB disabled/degraded.
    """
    status = _db_status()
    if not status["ready"]:
        return {"ready": False, "db": status["db"], "event": None}

    sql = """
        select
          event_id,
          kind,
          source,
          namespace,
          correlation_id,
          parent_event_id,
          received_at,
          method,
          host,
          path,
          remote_addr,
          status_code,
          headers_json,
          body_sha256,
          json_parsed,
          verify_status,
          verify_reason,
          dedupe_key,
          body_raw
        from events
        where event_id = ?
        limit 1
    """

    try:
        c = connect()
        r = _fetchone_dict(c, sql, (event_id,))
    except Exception as e:
        return {
            "ready": False,
            "db": {**status["db"], "mode": "error", "detail": str(e)},
            "event": None,
        }
    finally:
        try:
            c.close()
        except Exception:
            pass

    if not r:
        return {"ready": True, "db": status["db"], "event": None}

    evt = {
        "event_id": r.get("event_id"),
        "kind": r.get("kind"),
        "source": r.get("source"),
        "namespace": r.get("namespace"),
        "correlation_id": r.get("correlation_id"),
        "parent_event_id": r.get("parent_event_id"),
        "received_at": r.get("received_at"),
        "method": r.get("method"),
        "host": r.get("host"),
        "path": r.get("path"),
        "remote_addr": r.get("remote_addr"),
        "status_code": r.get("status_code"),
        "headers_json": r.get("headers_json"),
        "body_sha256": r.get("body_sha256"),
        "json_parsed": r.get("json_parsed"),
        "json_obj": _maybe_parse_json(r.get("json_parsed"), include_json_obj),
        "verify_status": r.get("verify_status"),
        "verify_reason": r.get("verify_reason"),
        "dedupe_key": r.get("dedupe_key"),
    }
    if include_body:
        evt["body_raw"] = _body_to_text(r.get("body_raw"), body_max_chars)

    return {"ready": True, "db": status["db"], "event": evt}


@router.get("/stats/summary")
async def stats_summary() -> Dict[str, Any]:
    """
    Minimal stats for demos/ops. Always returns HTTP 200.
    """
    status = _db_status()
    if not status["ready"]:
        return {
            "ready": False,
            "db": status["db"],
            "stats": {"events_total": 0, "by_source": {}, "by_kind": {}, "by_namespace": {}},
        }

    try:
        c = connect()
        total_row = _fetchone_dict(c, "select count(*) as n from events", ())
        by_source = _fetchall_dicts(c, "select source, count(*) as n from events group by source", ())
        by_kind = _fetchall_dicts(c, "select kind, count(*) as n from events group by kind", ())
        by_namespace = _fetchall_dicts(
            c, "select namespace, count(*) as n from events group by namespace", ()
        )
        total = int((total_row or {}).get("n", 0))
    except Exception as e:
        return {
            "ready": False,
            "db": {**status["db"], "mode": "error", "detail": str(e)},
            "stats": {"events_total": 0, "by_source": {}, "by_kind": {}, "by_namespace": {}},
        }
    finally:
        try:
            c.close()
        except Exception:
            pass

    return {
        "ready": True,
        "db": status["db"],
        "stats": {
            "events_total": total,
            "by_source": {r.get("source"): r.get("n") for r in by_source if r.get("source")},
            "by_kind": {r.get("kind"): r.get("n") for r in by_kind if r.get("kind")},
            "by_namespace": {
                r.get("namespace"): r.get("n") for r in by_namespace if r.get("namespace")
            },
        },
    }
