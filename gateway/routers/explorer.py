"""Read-only explorer derived from registered routes; never invokes integrations."""

import inspect
import os
import platform
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from gateway.observability import snapshot


def prevent_caching(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(
    prefix="/explorer", tags=["explorer"], dependencies=[Depends(prevent_caching)]
)


def describe_type(value):
    if value is None:
        return None
    result = {
        "type": getattr(value, "__name__", str(value)),
        "module": getattr(value, "__module__", None),
    }
    schema = getattr(value, "model_json_schema", None)
    if callable(schema):
        try:
            result["schema"] = schema()
        except Exception:
            result["schema_status"] = "unavailable"
    return result


def dependencies(dep, seen=None):
    seen = set() if seen is None else seen
    if id(dep) in seen:
        return []
    seen.add(id(dep))
    return [
        {
            "function": getattr(d.call, "__qualname__", str(d.call)),
            "module": getattr(d.call, "__module__", None),
            "dependencies": dependencies(d, seen),
        }
        for d in getattr(dep, "dependencies", [])
    ]


@router.get("/metadata")
async def metadata(request: Request):
    routes = []
    recent = snapshot()
    for route in request.app.routes:
        if not isinstance(route, APIRoute):
            continue
        item = {
            "path": route.path,
            "methods": sorted(route.methods),
            "family": route.tags or [route.endpoint.__module__],
            "endpoint": route.endpoint.__qualname__,
            "module": route.endpoint.__module__,
            "status": "registered; availability requires a request",
            "status_code": route.status_code or 200,
        }
        try:
            item.update(
                response_model=describe_type(route.response_model),
                request_model=describe_type(getattr(route.body_field, "type_", None)),
                parameters=[
                    {
                        "name": p.name,
                        "required": p.required,
                        "type": describe_type(p.type_),
                    }
                    for p in route.dependant.path_params
                    + route.dependant.query_params
                    + route.dependant.body_params
                ],
                dependencies=dependencies(route.dependant),
                async_handler=inspect.iscoroutinefunction(route.endpoint),
            )
        except Exception:
            item["metadata_status"] = "partially unavailable"
        item["last_observation"] = next(
            (
                t
                for t in reversed(recent)
                if t["path"] == route.path and t["method"] in route.methods
            ),
            None,
        )
        routes.append(item)
    packages = {}
    for name in ("fastapi", "starlette", "pydantic", "uvicorn"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = "unavailable"
    return {
        "routes": routes,
        "runtime": {
            "python": platform.python_version(),
            "packages": packages,
            "pid": os.getpid(),
            "telemetry": "200 completed requests per worker; volatile; explorer and static requests excluded",
        },
        "flow": [
            {
                "id": "ingress",
                "name": "Ingress / application boundary",
                "detail": "Traefik is documented in docs/006_runbooks/11_hetzner_api_ingress.md; deployment presence and latency unavailable",
            },
            {
                "id": "asgi",
                "name": "Uvicorn / ASGI",
                "detail": "Dockerfile launches gateway.app:app. ASGI lifetime and response start measured",
            },
            {
                "id": "framework",
                "name": "FastAPI / Starlette",
                "detail": "Registered route introspection; routing and dependency substage durations unavailable",
            },
            {
                "id": "validation",
                "name": "Pydantic validation",
                "detail": "Route models shown where declared; webhook takes raw Request and manually parses JSON; validation duration unavailable",
            },
            {
                "id": "handler",
                "name": "Route handler",
                "detail": "Select a route to inspect its actual endpoint and dependencies",
            },
            {
                "id": "envelope",
                "name": "Webhook envelope / idempotency",
                "detail": "gateway.routers.webhooks dictionary envelope (no EventEnvelope model). gateway.db.events_store hashes source + path + body SHA-256; INSERT OR IGNORE",
            },
            {
                "id": "ledger",
                "name": "SQLite ledger",
                "detail": "gateway.db.events_store.persist_inbound_event; webhook persistence span includes schema, hashing, write and commit",
            },
            {
                "id": "oauth",
                "name": "docusign OAuth",
                "detail": "Registered jwt-test calls requests.post oauth/token then requests.get oauth/userinfo. Ping is local only; explorer never invokes OAuth",
            },
            {
                "id": "monitor",
                "name": "Monitor / events",
                "detail": "Existing /webhooks/monitor/ui and SSE preserved. /events endpoints read the SQLite ledger",
            },
        ],
    }


@router.get("/traces")
async def trace_list():
    return {
        "traces": snapshot()[::-1],
        "unavailable": [
            "ingress latency",
            "routing duration",
            "Pydantic duration",
            "historical event durations",
        ],
    }


@router.get("/ui", response_class=HTMLResponse)
async def ui():
    return HTMLResponse(
        Path(__file__).with_name("explorer.html").read_text(encoding="utf-8"),
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                "default-src 'none'; script-src 'self'; style-src 'self'; "
                "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"
            ),
        },
    )
