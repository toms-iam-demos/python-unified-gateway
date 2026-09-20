import os
import unittest
from unittest.mock import patch, AsyncMock
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel
from gateway.app import create_app
from gateway.observability import traces, lock
from gateway.routers import explorer, webhooks
from test_connect_hmac import KEY, BODY, sign


class ExplorerTests(unittest.TestCase):
    def setUp(self):
        with lock:
            traces.clear()
        with patch.dict(os.environ, {"GATEWAY_EXPLORER_ENABLED": "1"}):
            self.app = create_app()
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def test_live_metadata_models_and_unregistered_router(self):
        self.client.get("/docusign/ping")
        data = self.client.get("/explorer/metadata").json()
        routes = data["routes"]
        ping = next(r for r in routes if r["path"] == "/docusign/ping")
        self.assertEqual(ping["module"], "gateway.routers.docusign")
        self.assertIn("schema", ping["response_model"])
        self.assertEqual(ping["last_observation"]["status_code"], 200)
        self.assertFalse(
            any(r["module"] == "gateway.routers.docusign_ping" for r in routes)
        )

    def test_measured_timing_and_privacy(self):
        self.client.get(
            "/health?secret=DO_NOT_STORE", headers={"authorization": "DO_NOT_STORE"}
        )
        trace = self.client.get("/explorer/traces").json()["traces"][0]
        self.assertEqual(trace["path"], "/health")
        self.assertGreaterEqual(trace["duration_ms"], trace["response_start_ms"])
        self.assertNotIn("DO_NOT_STORE", str(trace))
        self.client.get("/explorer/ui")
        self.client.get("/static/explorer.js")
        self.assertEqual(len(traces), 1)

    def test_webhook_spans_and_monitor_preserved(self):
        original = self.client.get("/webhooks/monitor/ui").text
        self.assertIn("/static/monitor.js", original)
        self.assertNotIn("cdn.jsdelivr.net", original)
        script = self.client.get("/static/monitor.js")
        self.assertEqual(script.status_code, 200)
        self.assertIn("/events/latest?limit=80&include_body=0&include_json_obj=0", script.text)
        self.assertIn("summary polling", script.text)
        with patch.dict(
            os.environ, {"DOCUSIGN_CONNECT_HMAC_SECRET": KEY}
        ), patch.object(
            webhooks,
            "persist_inbound_event",
            return_value={"persisted": True, "event_id": "test-event"},
        ), patch.object(
            webhooks, "_broadcast_event", new_callable=AsyncMock
        ):
            response = self.client.post(
                "/webhooks/docusign",
                content=BODY,
                headers={"x-docusign-signature-1": sign()},
            )
        self.assertEqual(response.status_code, 200)
        trace = self.client.get("/explorer/traces").json()["traces"][0]
        self.assertEqual(trace["event_id"], "test-event")
        self.assertEqual(len(trace["spans"]), 2)
        self.assertNotIn("synthetic-test", str(trace))

    def test_bounded_buffer_errors_and_unmatched_paths(self):
        for _ in range(205):
            self.client.get("/health")
        self.assertEqual(len(traces), 200)
        self.client.get("/unknown-private-value")
        self.assertEqual(traces[-1]["path"], "unmatched")
        self.assertEqual(traces[-1]["status_code"], 404)
        self.client.post("/webhooks/docusign", content=b"no signature")
        self.assertEqual(traces[-1]["spans"][0]["status"], "failed")

    def test_degraded_ledger(self):
        with patch.dict(os.environ, {"GATEWAY_DB_ENABLED": "0"}):
            result = self.client.get("/events/latest").json()
        self.assertFalse(result["ready"])
        self.assertEqual(self.client.get("/explorer/metadata").status_code, 200)

    def test_dynamic_request_models_and_dependencies(self):
        class Payload(BaseModel):
            value: int

        def dependency():
            return True

        local = FastAPI()

        @local.post("/dynamic")
        def dynamic(body: Payload, check=Depends(dependency)):
            return body

        local.include_router(explorer.router)
        with TestClient(local) as client:
            route = client.get("/explorer/metadata").json()["routes"][0]
        self.assertEqual(route["request_model"]["type"], "Payload")
        self.assertTrue(route["dependencies"])

    def test_oauth_spans_without_network(self):
        from gateway.routers import docusign_jwt_test as ds
        from unittest.mock import Mock

        token = Mock(status_code=200)
        token.json.return_value = {"access_token": "PRIVATE_TOKEN"}
        userinfo = Mock(status_code=200)
        userinfo.json.return_value = {"sub": "test"}
        with patch.object(ds, "_require_env", return_value="test"), patch.object(
            ds, "_read_private_key", return_value="test"
        ), patch.object(
            ds.jwt, "encode", return_value="PRIVATE_ASSERTION"
        ), patch.object(
            ds.requests, "post", return_value=token
        ), patch.object(
            ds.requests, "get", return_value=userinfo
        ):
            self.assertEqual(self.client.get("/docusign/jwt-test").status_code, 200)
        trace = traces[-1]
        self.assertEqual(
            [s["name"] for s in trace["spans"]],
            ["docusign OAuth token", "docusign OAuth userinfo"],
        )
        self.assertNotIn("PRIVATE", str(trace))

    def test_explorer_disabled_by_default_without_affecting_monitor(self):
        with patch.dict(os.environ, {}, clear=True), TestClient(create_app()) as client:
            for path in ("/explorer/ui", "/explorer/metadata", "/explorer/traces"):
                self.assertEqual(client.get(path).status_code, 404)
            self.assertEqual(client.get("/webhooks/monitor/ui").status_code, 200)
            self.assertEqual(client.get("/static/monitor.js").status_code, 200)
            self.assertFalse(
                any(
                    p.startswith("/explorer")
                    for p in client.get("/openapi.json").json()["paths"]
                )
            )
        self.assertEqual(len(traces), 0)

    def test_operator_responses_not_cached_and_ui_uses_external_assets(self):
        from html.parser import HTMLParser

        class Assets(HTMLParser):
            def __init__(self):
                super().__init__()
                self.sources = []
                self.inline_script = False
                self.inline_style = False

            def handle_starttag(self, tag, attrs):
                attributes = dict(attrs)
                if tag == "script":
                    self.inline_script |= "src" not in attributes
                    self.sources.append(attributes.get("src"))
                if tag == "link":
                    self.sources.append(attributes["href"])
                self.inline_style |= tag == "style" or "style" in attributes

        for path in ("/explorer/ui", "/explorer/metadata", "/explorer/traces"):
            response = self.client.get(path)
            self.assertEqual(response.headers["cache-control"], "no-store")
        ui = self.client.get("/explorer/ui")
        self.assertNotIn("unsafe-inline", ui.headers["content-security-policy"])
        parser = Assets()
        parser.feed(ui.text)
        self.assertFalse(parser.inline_script)
        self.assertFalse(parser.inline_style)
        for source in parser.sources:
            self.assertEqual(self.client.get("/explorer/" + source).status_code, 200)

    def test_unhandled_exception_is_traced_without_leaking_details(self):
        @self.app.get("/test-failure")
        async def failure():
            raise RuntimeError("PRIVATE_ERROR_DETAIL")

        with TestClient(self.app, raise_server_exceptions=False) as client:
            self.assertEqual(client.get("/test-failure").status_code, 500)
            trace = client.get("/explorer/traces").json()["traces"][0]
        self.assertEqual(trace["status_code"], 500)
        self.assertNotIn("PRIVATE_ERROR_DETAIL", str(trace))
        self.client.get("/health")
        self.assertEqual(traces[-1]["path"], "/health")
