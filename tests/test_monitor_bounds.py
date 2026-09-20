import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from gateway.db import init_db

MODULE = Path(__file__).resolve().parents[1] / 'gateway/routers/events.py'
spec = importlib.util.spec_from_file_location('bounded_events', MODULE)
events = importlib.util.module_from_spec(spec)
spec.loader.exec_module(events)

class MonitorBounds(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / 'events.db')
        env = patch.dict(os.environ, {'GATEWAY_DB_PATH': self.path, 'GATEWAY_DB_ENABLED':'1'})
        env.start(); self.addCleanup(env.stop)
        schema = patch.object(init_db, '_SCHEMA_APPLIED', False)
        schema.start(); self.addCleanup(schema.stop)
        self.assertTrue(init_db.ensure_schema().ready)
        payload = json.dumps({'blob':'x' * (2 * 1024 * 1024)})
        with sqlite3.connect(self.path) as db:
            for i in range(80):
                db.execute('INSERT INTO events (event_id,kind,source,correlation_id,received_at,headers_json,body_raw,json_parsed,verify_status,body_sha256,dedupe_key) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                           (str(i),'inbound_http','docusign',str(i),f'2026-09-09T00:00:{i:02d}Z','{}',payload.encode(),payload,'verified','test-hash',str(i)))
        app = FastAPI(); app.include_router(events.router)
        self.client = TestClient(app); self.addCleanup(self.client.close)

    def test_large_history_summary_remains_small(self):
        response = self.client.get('/events/latest?limit=80')
        self.assertEqual(response.status_code, 200)
        self.assertLess(len(response.content), 100000)
        rows = response.json()['events']; self.assertEqual(len(rows),80)
        self.assertTrue(all(r['json_parsed'] is None and 'body_raw' not in r for r in rows))

    def test_legacy_full_poll_is_also_bounded(self):
        tracemalloc.start()
        self.addCleanup(tracemalloc.stop)
        response = self.client.get('/events/latest?limit=80&include_body=1&include_json_obj=1&body_max_chars=200000')
        self.assertLess(tracemalloc.get_traced_memory()[1], 20 * 1024 * 1024)
        self.assertLess(len(response.content), 450000)
        row = response.json()['events'][0]
        self.assertEqual(len(row['body_raw']),4000)
        self.assertTrue(row['body_truncated']); self.assertTrue(row['json_omitted'])
        self.assertIsNone(row['json_obj'])

    def test_selected_event_preview_and_original_preserved(self):
        response = self.client.get('/events/1?body_max_chars=16000')
        row = response.json()['event']
        self.assertEqual(len(row['body_raw']),16000)
        self.assertTrue(row['json_omitted'])
        with sqlite3.connect(self.path) as db:
            size = db.execute("SELECT length(body_raw) FROM events WHERE event_id='1'").fetchone()[0]
        self.assertGreater(size, 2*1024*1024)

    def test_small_json_is_parsed(self):
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE events SET body_raw=?,json_parsed=? WHERE event_id='1'", (b'{"ok":true}', '{"ok":true}'))
        row = self.client.get('/events/1').json()['event']
        self.assertEqual(row['json_obj'], {'ok':True})
        self.assertFalse(row['json_omitted']); self.assertFalse(row['body_truncated'])

if __name__ == '__main__': unittest.main()
