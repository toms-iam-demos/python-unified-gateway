import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from gateway.observability import TraceMiddleware
from gateway.routers import (
    docusign,
    docusign_jwt_test,
    events,
    explorer,
    health,
    webhooks,
    workflows,
)


def create_app() -> FastAPI:
    app = FastAPI(title="Python Unified Gateway")
    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent / "static"),
        name="static",
    )
    app.include_router(health.router)
    app.include_router(webhooks.router)
    app.include_router(events.router)
    app.include_router(docusign.router)
    app.include_router(docusign_jwt_test.router, prefix="/docusign")

    if os.getenv("GATEWAY_WORKFLOWS_ENABLED", "0").strip() == "1":
        app.include_router(workflows.router)

    # Operator access remains an edge responsibility. Enable only after the
    # existing ingress policy protects /explorer/* (or on a loopback-only host).
    if os.getenv("GATEWAY_EXPLORER_ENABLED", "0").strip() == "1":
        app.include_router(explorer.router)
        app.add_middleware(TraceMiddleware)
    return app


app = create_app()
