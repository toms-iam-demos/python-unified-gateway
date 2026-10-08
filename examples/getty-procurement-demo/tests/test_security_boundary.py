from fastapi.testclient import TestClient
from app import main
from app.security import RequestSizeLimit
import asyncio

def test_cross_site_and_oversized_requests():
    headers = {"x-demo-token": getattr(main, "TOKEN", "")}
    with TestClient(main.app, headers=headers) as client:
        assert client.post("/api/seed", json={}, headers={"sec-fetch-site": "cross-site"}).status_code == 403
        assert client.post("/api/seed", content=b"x" * 131073).status_code == 413

def test_chunk_limit_ignores_claimed_length():
    async def check():
        invoked = False
        async def downstream(scope, receive, send):
            nonlocal invoked
            invoked = True
        chunks = iter([{"type": "http.request", "body": b"123", "more_body": True}, {"type": "http.request", "body": b"456", "more_body": False}])
        async def receive(): return next(chunks)
        messages = []
        async def send(message): messages.append(message)
        await RequestSizeLimit(downstream, limit=5)({"type": "http", "method": "POST", "headers": [(b"content-length", b"1")]}, receive, send)
        assert messages[0]["status"] == 413
        assert not invoked
    asyncio.run(check())
