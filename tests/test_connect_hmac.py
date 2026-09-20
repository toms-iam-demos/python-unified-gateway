import base64
import hashlib
import hmac
import os
import sqlite3
import tempfile
import unittest
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

    def test_verified_request_preserves_existing_fail_open_persistence_policy(self):
        self.persist.return_value = {"persisted": False, "db_mode": "degraded"}
        response = self.post(headers={"X-DocuSign-Signature-1": sign()})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["persisted"])
        self.broadcast.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
