"""Bounded metadata-only telemetry. No bodies, headers, tokens or query strings."""

from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from threading import Lock
from time import perf_counter
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

traces = deque(maxlen=200)
lock = Lock()
current: ContextVar[dict | None] = ContextVar("pug_trace", default=None)


def snapshot() -> list[dict]:
    """Completed traces are immutable after publication; return a stable list."""
    with lock:
        return list(traces)


@contextmanager
def span(name: str):
    trace = current.get()
    if trace is None:
        yield
        return

    start = perf_counter()
    status = "completed"
    try:
        yield
    except BaseException:
        status = "failed"
        raise
    finally:
        trace["spans"].append(
            {
                "name": name,
                "offset_ms": round((start - trace["start"]) * 1000, 3),
                "duration_ms": round((perf_counter() - start) * 1000, 3),
                "status": status,
                "provenance": "measured",
            }
        )


class TraceMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        path = scope.get("path", "")
        excluded = any(
            path == prefix or path.startswith(prefix + "/")
            for prefix in ("/explorer", "/static")
        )
        if scope["type"] != "http" or excluded:
            return await self.app(scope, receive, send)

        trace = {
            "id": str(uuid4()),
            "method": scope["method"],
            "start": perf_counter(),
            "received_at": datetime.now(timezone.utc).isoformat(),
            "spans": [],
            "status_code": None,
        }
        token = current.set(trace)

        async def measured_send(message: Message):
            if message["type"] == "http.response.start":
                trace["status_code"] = message["status"]
                trace["response_start_ms"] = round(
                    (perf_counter() - trace["start"]) * 1000, 3
                )
            await send(message)

        try:
            await self.app(scope, receive, measured_send)
        except Exception:
            trace["status_code"] = trace["status_code"] or 500
            trace["outcome"] = "unhandled error"
            raise
        finally:
            route = scope.get("route")
            trace["path"] = getattr(route, "path", "unmatched")
            trace["duration_ms"] = round(
                (perf_counter() - trace.pop("start")) * 1000, 3
            )
            trace["provenance"] = "measured ASGI lifetime (includes streaming)"
            try:
                with lock:
                    traces.append(trace)
            finally:
                current.reset(token)
