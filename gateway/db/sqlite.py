from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional


def db_path() -> str:
    return os.getenv("GATEWAY_DB_PATH", "/app/data/gateway.db")


def connect(path: Optional[str] = None) -> sqlite3.Connection:
    """
    Open a SQLite connection with WAL and sane pragmas.
    This function may raise sqlite3.OperationalError if the path is unwritable.
    """
    p = Path(path or db_path())
    p.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(p),
        timeout=5.0,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row

    # Pragmas (WAL is the non-negotiable concurrency baseline for webhook bursts)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn
