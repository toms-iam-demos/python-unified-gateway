import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from gateway.db.init_db import DBStatus
from gateway.routers import health


class ReadinessTests(unittest.TestCase):
    def test_readiness_hides_only_degraded_database_detail(self):
        app = FastAPI()
        app.include_router(health.router)
        cases = (
            (DBStatus(True, False, "degraded", "synthetic-private-path"), "database unavailable"),
            (DBStatus(True, True, "ok", "schema already applied"), "schema already applied"),
            (DBStatus(False, False, "disabled", "GATEWAY_DB_ENABLED=0"), "GATEWAY_DB_ENABLED=0"),
        )
        with TestClient(app) as client:
            for status, detail in cases:
                with self.subTest(mode=status.mode), patch.object(
                    health, "ensure_schema", return_value=status
                ) as ensure_schema:
                    response = client.get("/health/ready")
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(
                        response.json(),
                        {
                            "ready": status.ready,
                            "db": {"enabled": status.enabled, "mode": status.mode, "detail": detail},
                        },
                    )
                    ensure_schema.assert_called_once_with()

            with patch.object(health, "ensure_schema") as ensure_schema:
                response = client.get("/health")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json(), {"status": "ok", "source": "python-unified-gateway"}
                )
                ensure_schema.assert_not_called()
