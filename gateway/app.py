import os
from pathlib import Path

from fastapi import Depends, FastAPI
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
    app = FastAPI(title="Python Unified Gateway", swagger_ui_parameters={"supportedSubmitMethods": ["get"], "persistAuthorization": False, "filter": True})
    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent / "static"),
        name="static",
    )
    app.include_router(health.router)
    app.include_router(webhooks.router)
    app.include_router(events.router)
    app.include_router(docusign.router)
    app.include_router(docusign_jwt_test.router, prefix="/docusign", dependencies=[Depends(workflows.operator)])

    if os.getenv("GATEWAY_WORKFLOWS_ENABLED", "0").strip() == "1":
        app.include_router(workflows.router)

    if os.getenv("GATEWAY_FULL_DOCUSIGN_API_ENABLED", "0").strip() == "1":
        from gateway.routers.full_api import install
        install(app)

    # Operator access remains an edge responsibility. Enable only after the
    # existing ingress policy protects /explorer/* (or on a loopback-only host).
    if os.getenv("GATEWAY_EXPLORER_ENABLED", "0").strip() == "1":
        app.include_router(explorer.router)
        app.add_middleware(TraceMiddleware)
    return app


app = create_app()
