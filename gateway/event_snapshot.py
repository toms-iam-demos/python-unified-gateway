"""Single bounded, process-memory snapshot; no background jobs or disk writes."""
import asyncio
import json
import time
from datetime import datetime, timezone


class SnapshotUnavailable(Exception):
    pass


class SnapshotCache:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._value = None
        self._captured = 0.0

    async def get(self, loader, refresh=False):
        async with self._lock:
            if self._value is not None and (not refresh or time.monotonic() - self._captured < 2):
                return {**self._value, "cached": True}
            data = await loader(limit=200, include_body=1, include_json_obj=1, body_max_chars=4000)
            if data.get("ready") is not True or not isinstance(data.get("events"), list):
                raise SnapshotUnavailable("The event store is unavailable. The previous snapshot is preserved.")
            value = {
                "ready": True,
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "limit": 200,
                "preview_bytes": 4000,
                "returned": len(data["events"]),
                "events": data["events"],
            }
            if len(json.dumps(value).encode()) > 8 * 1024 * 1024:
                raise SnapshotUnavailable("The snapshot exceeds its memory budget. The previous snapshot is preserved.")
            self._value = value
            self._captured = time.monotonic()
            return {**value, "cached": False}
