import os
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse
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
    full_catalog = os.getenv("GATEWAY_FULL_DOCUSIGN_API_ENABLED", "0").strip() == "1"
    private_catalog = full_catalog and bool(os.getenv("GATEWAY_OBSERVED_API_SPEC_PATH", "").strip())
    doc_paths = {"docs_url": None, "redoc_url": None, "openapi_url": None} if private_catalog else {}
    app = FastAPI(title="Python Unified Gateway", swagger_ui_parameters={"supportedSubmitMethods": ["get"], "persistAuthorization": False, "filter": True}, **doc_paths)
    if private_catalog:
        dependencies = [Depends(workflows.operator)]

        @app.middleware("http")
        async def private_document_cache_control(request: Request, call_next):
            response = await call_next(request)
            root = request.scope.get("root_path", "").rstrip("/")
            path = request.scope["path"].removeprefix(root).rstrip("/")
            if path in {"/docs", "/redoc", "/openapi.json"}:
                response.headers["Cache-Control"] = "no-store"
            return response

        @app.get("/openapi.json", include_in_schema=False, dependencies=dependencies)
        def private_openapi():
            return JSONResponse(app.openapi(), headers={"Cache-Control": "no-store"})

        @app.get("/docs", include_in_schema=False, dependencies=dependencies)
        def private_swagger(request: Request):
            root = request.scope.get("root_path", "").rstrip("/")
            response = get_swagger_ui_html(openapi_url=root + "/openapi.json", title=app.title,
                swagger_ui_parameters=app.swagger_ui_parameters)
            response.headers["Cache-Control"] = "no-store"
            return response

        @app.get("/redoc", include_in_schema=False, dependencies=dependencies)
        def private_redoc(request: Request):
            root = request.scope.get("root_path", "").rstrip("/")
            response = get_redoc_html(openapi_url=root + "/openapi.json", title=app.title)
            response.headers["Cache-Control"] = "no-store"
            return response
    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent / "static"),
        name="static",
    )
    app.include_router(health.router)
    app.include_router(webhooks.router)
    from gateway.events_ui import router as events_ui_router
    app.include_router(events_ui_router)
    app.include_router(events.router)
    app.include_router(docusign.router)
    app.include_router(docusign_jwt_test.router, prefix="/docusign", dependencies=[Depends(workflows.operator)])

    if os.getenv("GATEWAY_WORKFLOWS_ENABLED", "0").strip() == "1":
        app.include_router(workflows.router)

    if full_catalog:
        from gateway.routers.full_api import install
        install(app)

    # Operator access remains an edge responsibility. Enable only after the
    # existing ingress policy protects /explorer/* (or on a loopback-only host).
    if os.getenv("GATEWAY_EXPLORER_ENABLED", "0").strip() == "1":
        app.include_router(explorer.router)
        app.add_middleware(TraceMiddleware)
    if os.getenv("PUG_AUDIT_ENABLED", "0").strip() == "1":
        from gateway.security_audit import SecurityAuditMiddleware, router as audit_router
        app.include_router(audit_router)
        app.add_middleware(SecurityAuditMiddleware)
    from gateway.presentation import PresentationMiddleware
    app.add_middleware(PresentationMiddleware)
    return app


app = create_app()
