"""Regression coverage using synthetic events and disposable SQLite only."""

import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from gateway.db import events_store, init_db


class DuplicateDeliveryIdentifierTests(unittest.TestCase):
    def test_duplicate_delivery_returns_stored_identifiers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "events.db")
            with patch.dict(
                os.environ,
                {"GATEWAY_DB_PATH": path, "GATEWAY_DB_ENABLED": "1"},
            ), patch.object(init_db, "_SCHEMA_APPLIED", False), patch.object(
                init_db, "_LAST_ERROR", ""
            ):
                event = dict(
                    source="synthetic-test",
                    method="POST",
                    host="synthetic.invalid",
                    path="/synthetic/duplicate",
                    remote_addr=None,
                    headers={},
                    raw_body=b'{"event":"synthetic-duplicate"}',
                    json_parsed={"event": "synthetic-duplicate"},
                    verify_status="verified",
                    verify_reason="synthetic-test",
                )
                first = events_store.persist_inbound_event(**event)
                second = events_store.persist_inbound_event(
                    **event, correlation_id="synthetic-retry-correlation"
                )
                self.assertTrue(first["persisted"])
                self.assertTrue(second["persisted"])
                with sqlite3.connect(path) as db:
                    rows = db.execute(
                        "SELECT event_id, correlation_id FROM events"
                    ).fetchall()
                self.assertEqual(len(rows), 1)
                stored_identifiers = rows[0]
                self.assertEqual(
                    (first["event_id"], first["correlation_id"]),
                    stored_identifiers,
                )
                self.assertEqual(
                    (second["event_id"], second["correlation_id"]),
                    stored_identifiers,
                    "Duplicate delivery must return identifiers of the stored row",
                )


if __name__ == "__main__":
    unittest.main()
