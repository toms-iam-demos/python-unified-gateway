"""Verify ledger I/O cannot monopolize the ASGI event loop."""

import asyncio
import os
import threading
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from gateway.app import create_app
from gateway.routers import webhooks
from test_connect_hmac import BODY, KEY, sign


class WebhookConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_health_completes_while_ledger_write_is_waiting(self):
        started = threading.Event()
        release = threading.Event()
        worker_thread = []
        loop_thread = threading.get_ident()

        def persist(**kwargs):
            worker_thread.append(threading.get_ident())
            started.set()
            release.wait(timeout=3)
            return {"persisted": True, "event_id": "synthetic"}

        with patch.dict(
            os.environ, {"DOCUSIGN_CONNECT_HMAC_SECRET": KEY}
        ), patch.object(
            webhooks, "persist_inbound_event", side_effect=persist
        ), patch.object(
            webhooks, "_broadcast_event", new_callable=AsyncMock
        ), patch.object(
            webhooks, "_webhook_events", []
        ):
            transport = httpx.ASGITransport(app=create_app())
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                task = asyncio.create_task(
                    client.post(
                        "/webhooks/docusign",
                        content=BODY,
                        headers={"x-docusign-signature-1": sign()},
                    )
                )
                try:
                    self.assertTrue(await asyncio.to_thread(started.wait, 2))
                    self.assertNotEqual(worker_thread[0], loop_thread)
                    health = await asyncio.wait_for(client.get("/health"), timeout=1)
                    self.assertEqual(health.status_code, 200)
                    self.assertFalse(task.done())
                finally:
                    release.set()
                    response = await task
                self.assertEqual(response.status_code, 200)
