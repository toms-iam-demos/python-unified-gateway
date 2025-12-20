from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from gateway.db.init_db import ensure_schema
from gateway.db.sqlite import connect

log = logging.getLogger("gateway.events_store")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def persist_inbound_event(
    *,
    source: str,
    method: str,
    host: str,
    path: str,
    remote_addr: Optional[str],
    headers: Dict[str, Any],
    raw_body: bytes,
    json_parsed: Optional[Dict[str, Any]],
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Best-effort persistence. Never raises to caller.
    Returns an envelope describing persistence result and generated ids.
    """
    status = ensure_schema()
    if not status.ready:
        return {"persisted": False, "db_mode": status.mode, "db_detail": status.detail}

    event_id = str(uuid.uuid4())
    corr = correlation_id or str(uuid.uuid4())
    received_at = _utc_now_iso()

    headers_json = json.dumps(headers, default=str)
    body_sha256 = _sha256_bytes(raw_body)
    json_text = json.dumps(json_parsed, default=str) if json_parsed is not None else None

    # Dedupe key: stable hash of source+path+body
    dedupe_key = _sha256_bytes(f"{source}|{path}|{body_sha256}".encode("utf-8"))

    try:
        conn = connect()
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO events (
                  event_id, kind, source, namespace,
                  correlation_id, parent_event_id, received_at,
                  method, host, path, remote_addr, status_code,
                  headers_json, body_raw, body_sha256, json_parsed,
                  verify_status, verify_reason, dedupe_key
                ) VALUES (
                  ?, 'inbound_http', ?, '',
                  ?, NULL, ?,
                  ?, ?, ?, ?, NULL,
                  ?, ?, ?, ?,
                  'unknown', NULL, ?
                )
                """,
                (
                    event_id, source,
                    corr, received_at,
                    method, host, path, remote_addr,
                    headers_json, raw_body, body_sha256, json_text,
                    dedupe_key,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        return {"persisted": True, "event_id": event_id, "correlation_id": corr, "db_mode": "ok"}
    except Exception:
        log.exception("DB write failed (degraded mode).")
        return {"persisted": False, "db_mode": "degraded", "db_detail": "write failed"}
