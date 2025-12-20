from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from gateway.db.sqlite import connect

log = logging.getLogger("gateway.db")


@dataclass(frozen=True)
class DBStatus:
    enabled: bool
    ready: bool
    mode: str  # ok|degraded|disabled
    detail: str


_SCHEMA_APPLIED = False
_LAST_ERROR = ""


def schema_path() -> Path:
    return Path(__file__).with_name("schema.sql")


def ensure_schema() -> DBStatus:
    """
    Best-effort: open DB, set pragmas, apply schema.
    Never raises; returns status describing what happened.
    """
    global _SCHEMA_APPLIED, _LAST_ERROR

    enabled = (str(__import__("os").getenv("GATEWAY_DB_ENABLED", "1")).strip() != "0")
    if not enabled:
        return DBStatus(enabled=False, ready=False, mode="disabled", detail="GATEWAY_DB_ENABLED=0")

    if _SCHEMA_APPLIED:
        return DBStatus(enabled=True, ready=True, mode="ok", detail="schema already applied")

    try:
        sql = schema_path().read_text(encoding="utf-8")
        conn = connect()
        try:
            conn.executescript(sql)
            _SCHEMA_APPLIED = True
            _LAST_ERROR = ""
            # confirm WAL (informational)
            jm = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            return DBStatus(enabled=True, ready=True, mode="ok", detail=f"schema applied; journal_mode={jm}")
        finally:
            conn.close()
    except Exception as e:
        _LAST_ERROR = repr(e)
        log.exception("DB ensure_schema failed (degraded mode).")
        return DBStatus(enabled=True, ready=False, mode="degraded", detail=_LAST_ERROR)


def last_error() -> str:
    return _LAST_ERROR

