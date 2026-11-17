import base64
import hashlib
import hmac
import json
import os
import sqlite3
import tempfile
import unittest
import uuid
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from gateway.routers import webhooks
from gateway.db import events_store, init_db

KEY = "test-only-key+/=not-a-real-secret"
BODY = b'{"event":"envelope-sent","data":{"envelopeId":"synthetic-test"}}'


def sign(body=BODY, key=KEY):
    return base64.b64encode(
        hmac.new(key.encode(), body, hashlib.sha256).digest()
    ).decode()


class ConnectHmacTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {"DOCUSIGN_CONNECT_HMAC_SECRET": KEY})
        env.start()
        self.addCleanup(env.stop)
        persistence = patch.object(
            webhooks, "persist_inbound_event", return_value={"persisted": True}
        )
        self.persist = persistence.start()
        self.addCleanup(persistence.stop)
        broadcast = patch.object(webhooks, "_broadcast_event", new_callable=AsyncMock)
        self.broadcast = broadcast.start()
        self.addCleanup(broadcast.stop)
        buffer = patch.object(webhooks, "_webhook_events", [])
        buffer.start()
        self.addCleanup(buffer.stop)
        app = FastAPI()
        app.include_router(webhooks.router)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def post(self, body=BODY, headers=None):
        return self.client.post(
            "/webhooks/docusign", content=body, headers=headers or {}
        )

    def assert_rejected(self, response, status=401):
        self.assertEqual(response.status_code, status)
        self.persist.assert_not_called()
        self.broadcast.assert_not_awaited()
        self.assertEqual(webhooks._webhook_events, [])

    def test_valid_signature_records_verification(self):
        response = self.post(headers={"X-DocuSign-Signature-1": sign()})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["persisted"])
        self.assertEqual(self.persist.call_args.kwargs["raw_body"], BODY)
        self.assertEqual(self.persist.call_args.kwargs["verify_status"], "verified")
        self.assertEqual(self.persist.call_args.kwargs["verify_reason"], "hmac-sha256")
        self.broadcast.assert_awaited_once()

    def test_failed_persistence_requests_redelivery(self):
        self.persist.return_value = {
            "persisted": False,
            "db_mode": "degraded",
            "db_detail": "synthetic-private-database-detail",
        }
        headers = {
            "X-DocuSign-Signature-1": sign(),
            "X-Correlation-Id": "synthetic-private-correlation",
            "X-Private-Header": "synthetic-private-header",
        }
        with self.assertLogs(webhooks.__name__, level="WARNING") as logs:
            response = self.post(headers=headers)
        self.assertEqual(
            [record.getMessage() for record in logs.records],
            ["Verified Docusign webhook not persisted; returning 503 for redelivery."],
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["retry-after"], "60")
        self.assertEqual(
            response.json(),
            {"status": "retry", "length": len(BODY), "persisted": False},
        )
        self.assertNotIn("synthetic-private", response.text)
        self.assertEqual(webhooks._webhook_events[0]["status"], "warn")
        self.broadcast.assert_awaited_once()

        self.persist.reset_mock()
        self.broadcast.reset_mock()
        webhooks._webhook_events.clear()
        with self.assertNoLogs(webhooks.__name__, level="WARNING"):
            self.assert_rejected(self.post(headers={"X-DocuSign-Signature-1": "invalid"}))

        self.persist.return_value = {"persisted": True}
        with self.assertNoLogs(webhooks.__name__, level="WARNING"):
            response = self.post(headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["persisted"])

    def test_monitor_hides_only_degraded_persistence_detail(self):
        for mode, detail, expected, status in (
            ("degraded", "synthetic-private-database-detail", "database unavailable", 503),
            ("disabled", "GATEWAY_DB_ENABLED=0", "GATEWAY_DB_ENABLED=0", 200),
        ):
            with self.subTest(mode=mode):
                original = {"persisted": False, "db_mode": mode, "db_detail": detail}
                self.persist.return_value = original
                response = self.post(headers={"X-DocuSign-Signature-1": sign()})
                self.assertEqual(response.status_code, status)
                self.assertFalse(response.json()["persisted"])
                feed = self.client.get("/webhooks/monitor").json()["events"]
                event = feed[-1]
                self.assertEqual(event["status"], "warn")
                self.assertEqual(
                    event["persistence"], {**original, "db_detail": expected}
                )
                self.assertEqual(self.broadcast.await_args.args[0], event)
                self.assertEqual(original["db_detail"], detail)

    def test_valid_request_persists_verification_in_real_sqlite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = directory + "/events.db"
            with patch.dict(
                os.environ, {"GATEWAY_DB_PATH": path, "GATEWAY_DB_ENABLED": "1"}
            ), patch.object(init_db, "_SCHEMA_APPLIED", False), patch.object(
                webhooks, "persist_inbound_event", events_store.persist_inbound_event
            ):
                response = self.post(headers={"X-DocuSign-Signature-1": sign()})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["persisted"])
                with sqlite3.connect(path) as db:
                    row = db.execute(
                        "SELECT verify_status, verify_reason, body_raw FROM events"
                    ).fetchone()
                self.assertEqual(row, ("verified", "hmac-sha256", BODY))

    def test_missing_signature(self):
        self.assert_rejected(self.post())

    def test_wrong_key(self):
        self.assert_rejected(
            self.post(headers={"X-DocuSign-Signature-1": sign(key="wrong")})
        )

    def test_tampered_body_including_whitespace(self):
        self.assert_rejected(
            self.post(BODY + b"\n", {"X-DocuSign-Signature-1": sign()})
        )

    def test_missing_key_fails_closed(self):
        os.environ.pop("DOCUSIGN_CONNECT_HMAC_SECRET")
        self.assert_rejected(self.post(headers={"X-DocuSign-Signature-1": sign()}), 503)

    def test_blank_key_fails_closed(self):
        os.environ["DOCUSIGN_CONNECT_HMAC_SECRET"] = "  "
        self.assert_rejected(self.post(), 503)

    def test_malformed_signatures_do_not_error(self):
        for value in ["%%%", "!" * 44, "a" * 44, "\u00e9" * 44]:
            with self.subTest(value=value):
                # ASGI headers use latin-1. Supply bytes for non-ASCII input.
                self.assert_rejected(
                    self.post(
                        headers={b"x-docusign-signature-1": value.encode("latin-1")}
                    )
                )

    def test_rotation_accepts_matching_second_header(self):
        response = self.post(
            headers={
                "X-DocuSign-Signature-1": sign(key="old-key"),
                "X-DocuSign-Signature-2": sign(),
            }
        )
        self.assertEqual(response.status_code, 200)

    def test_unrelated_header_cannot_authenticate(self):
        self.assert_rejected(self.post(headers={"X-Other-Signature-1": sign()}))

    def test_rejection_logs_do_not_expose_secrets_or_payload(self):
        with self.assertLogs("gateway.connect_hmac", level="WARNING") as captured:
            self.assert_rejected(
                self.post(headers={"X-DocuSign-Signature-1": sign(key="wrong")})
            )
        output = " ".join(captured.output)
        for private in [KEY, BODY.decode(), sign(key="wrong")]:
            self.assertNotIn(private, output)

    def test_duplicate_delivery_does_not_add_or_relabel_a_legacy_row(self):
        with tempfile.TemporaryDirectory() as directory:
            path = directory + "/events.db"
            with patch.dict(
                os.environ, {"GATEWAY_DB_PATH": path, "GATEWAY_DB_ENABLED": "1"}
            ), patch.object(init_db, "_SCHEMA_APPLIED", False), patch.object(
                webhooks, "persist_inbound_event", events_store.persist_inbound_event
            ):
                headers = {"X-DocuSign-Signature-1": sign()}
                self.assertTrue(self.post(headers=headers).json()["persisted"])
                with sqlite3.connect(path) as db:
                    db.execute(
                        "UPDATE events SET verify_status='unknown', verify_reason=NULL"
                    )
                self.assertTrue(self.post(headers=headers).json()["persisted"])
                with sqlite3.connect(path) as db:
                    rows = db.execute(
                        "SELECT verify_status, verify_reason FROM events"
                    ).fetchall()
                self.assertEqual(rows, [("unknown", None)])

    def test_unpersisted_event_is_not_acknowledged_but_stays_visible(self):
        for result in ({"persisted": False, "db_mode": "degraded"}, {"persisted": False}):
            with self.subTest(result=result):
                self.broadcast.reset_mock()
                self.persist.return_value = result
                response = self.post(headers={"X-DocuSign-Signature-1": sign()})
                self.assertEqual(response.status_code, 503)
                self.assertFalse(response.json()["persisted"])
                self.broadcast.assert_awaited_once()

    def test_disabled_ledger_still_acknowledges(self):
        self.persist.return_value = {"persisted": False, "db_mode": "disabled"}
        with self.assertLogs(webhooks.__name__, level="WARNING") as logs:
            response = self.post(headers={"X-DocuSign-Signature-1": sign()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [record.getMessage() for record in logs.records],
            ["Verified Docusign webhook acknowledged without a ledger receipt."],
        )

    def real_ledger(self, directory):
        return (
            patch.dict(os.environ, {"GATEWAY_DB_PATH": directory + "/events.db", "GATEWAY_DB_ENABLED": "1"}),
            patch.object(init_db, "_SCHEMA_APPLIED", False),
            patch.object(webhooks, "persist_inbound_event", events_store.persist_inbound_event),
        )

    def post_json(self, payload, extra_headers=None):
        body = json.dumps(payload).encode()
        return self.post(body, {"X-DocuSign-Signature-1": sign(body), **(extra_headers or {})})

    def test_connect_redelivery_with_new_retry_count_is_deduplicated(self):
        event = {"event": "envelope-completed", "retryCount": 0, "data": {"envelopeId": "synthetic-test"}}
        with tempfile.TemporaryDirectory() as directory:
            env, schema, persist = self.real_ledger(directory)
            with env, schema, persist:
                first = self.post_json(event)
                second = self.post_json({**event, "retryCount": 1})
                changed = self.post_json({**event, "retryCount": 2, "event": "envelope-voided"})
                with sqlite3.connect(directory + "/events.db") as db:
                    rows = db.execute("SELECT body_raw FROM events ORDER BY rowid").fetchall()
        self.assertEqual([r.status_code for r in (first, second, changed)], [200, 200, 200])
        self.assertEqual(len(rows), 2, "a retry adds no row; a different event does")
        self.assertIn(b'"retryCount": 0', rows[0][0], "the first delivery's original bytes are kept")
        self.assertIn(b"envelope-voided", rows[1][0])

    def test_dedupe_basis_only_strips_top_level_retry_count(self):
        self.assertIsNone(webhooks.dedupe_basis(None))
        self.assertIsNone(webhooks.dedupe_basis({"event": "x"}))
        self.assertIsNone(webhooks.dedupe_basis([{"retryCount": 1}]))
        nested = {"retryCount": 3, "data": {"retryCount": 9}}
        self.assertEqual(webhooks.dedupe_basis(nested), b'{"data":{"retryCount":9}}')

    def test_client_headers_cannot_set_ledger_correlation(self):
        supplied = "synthetic-client-correlation"
        with tempfile.TemporaryDirectory() as directory:
            env, schema, persist = self.real_ledger(directory)
            with env, schema, persist:
                response = self.post_json({"event": "envelope-sent"}, {"X-Correlation-Id": supplied, "X-Request-Id": supplied})
                with sqlite3.connect(directory + "/events.db") as db:
                    correlation, headers = db.execute("SELECT correlation_id, headers_json FROM events").fetchone()
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(correlation, supplied)
        self.assertEqual(str(uuid.UUID(correlation)), correlation)
        self.assertEqual(json.loads(headers)["x-correlation-id"], supplied, "kept as unverified input only")
        self.post(headers={"X-DocuSign-Signature-1": sign(), "X-Correlation-Id": supplied})
        self.assertNotIn("correlation_id", self.persist.call_args.kwargs)

    def test_oversized_body_rejected_before_verification(self):
        with patch.dict(os.environ, {"DOCUSIGN_CONNECT_MAX_BODY_BYTES": str(len(BODY))}):
            self.assertEqual(self.post(headers={"X-DocuSign-Signature-1": sign()}).status_code, 200)
            self.persist.reset_mock()
            self.broadcast.reset_mock()
            webhooks._webhook_events.clear()
            big = BODY + b" "
            with self.assertLogs(webhooks.__name__, level="WARNING") as logs:
                response = self.post(big, {"X-DocuSign-Signature-1": sign(big)})
            self.assert_rejected(response, 413)
            self.assertEqual([r.getMessage() for r in logs.records], ["connect_webhook_rejected reason=body_too_large"])
            # No Content-Length (chunked) is bounded by the streaming read.
            chunked = self.client.post("/webhooks/docusign", content=iter([BODY, b" "]),
                                       headers={"X-DocuSign-Signature-1": sign(big)})
            self.assert_rejected(chunked, 413)

    def test_body_limit_configuration_falls_back_to_default(self):
        for value in ("", "abc", "0", "-5"):
            with self.subTest(value=value), patch.dict(os.environ, {"DOCUSIGN_CONNECT_MAX_BODY_BYTES": value}):
                self.assertEqual(webhooks.max_body_bytes(), webhooks.DEFAULT_MAX_BODY_BYTES)
        with patch.dict(os.environ, {"DOCUSIGN_CONNECT_MAX_BODY_BYTES": "1024"}):
            self.assertEqual(webhooks.max_body_bytes(), 1024)


if __name__ == "__main__":
    unittest.main()
