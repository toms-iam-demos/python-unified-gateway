"""Website application factory; can also mount beside existing gateway routes."""
from pathlib import Path
import mimetypes
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.concurrency import run_in_threadpool
from .catalog import load_profile
from .navigation import GROUPS
from .security import authenticate
from .settings import Settings

ROOT = Path(__file__).parent
mimetypes.add_type("font/woff2", ".woff2")

def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    profile = load_profile(settings.profile_file)
    templates = Jinja2Templates(directory=ROOT / "templates")
    app = FastAPI(title="PUG www", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        if settings.require_auth:
            try:
                await run_in_threadpool(authenticate, request.headers.get("authorization", ""), settings)
            except HTTPException as exc:
                return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
        response = await call_next(request)
        response.headers.update({
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        })
        return response

    router = APIRouter()
    def page(request, template, **context):
        return templates.TemplateResponse(request=request, name=template, context={"profile": profile, "navigation": GROUPS, **context})

    @router.get("/")
    async def home(request: Request):
        return page(request, "home.html", title="PUG", entries=profile.entries[:3])

    @router.get("/catalog")
    @router.get("/demos")
    async def catalog(request: Request):
        return page(request, "catalog.html", title="Demo catalog", entries=profile.entries, categories=sorted({e.category for e in profile.entries}))

    @router.get("/catalog/{slug}")
    async def detail(request: Request, slug: str):
        entry = next((e for e in profile.entries if e.id == slug), None)
        if entry is None:
            raise HTTPException(404, "Example not found")
        return page(request, "detail.html", title=entry.title, entry=entry)

    @router.get("/api/v1/www/catalog")
    async def catalog_data():
        return {"entries": [e.model_dump() for e in profile.entries]}

    @router.get("/brand/{name}")
    async def brand(name: str):
        relative = profile.assets.get(name)
        if not relative or not settings.asset_directory:
            raise HTTPException(404, "Asset not found")
        base = settings.asset_directory.resolve()
        path = (base / relative).resolve()
        if not path.is_relative_to(base) or path.suffix.lower() not in {".svg", ".png", ".jpg", ".jpeg", ".webp", ".woff2"} or not path.is_file():
            raise HTTPException(404, "Asset not found")
        return FileResponse(path)

    pages = {
        "/build": ("Build", "Inspect the gateway API reference and integration contracts. The website does not enable additional provider writes."),
        "/resources": ("Resources", "Presenter guides, implementation notes and design documents belong with their demo. Secured artifact delivery is a separate capability and is not implemented by this website component."),
        "/demos/data-studio": ("Data Studio", "A proposed shared capability for configuring, generating and versioning demonstration datasets. This page does not provide a dataset generator."),
        "/workspaces/agents": ("Agents", "Development workups for agreement agents. This page does not establish a connected agent runtime."),
        "/workspaces/mcp": ("MCP", "Your MCP workspace. Its owner-selected identity is supplied by the external branding profile. This page does not start an MCP server."),
        "/workspaces/ham": ("HAM", "The separate enterprise emulation workspace. This website does not replace or start the HAM service."),
    }
    # Register fixed paths explicitly; a fallback must not swallow API errors.
    def register(path, heading, description):
        async def resource(request: Request):
            return page(request, "resource.html", title=heading, description=description)
        router.add_api_route(path, resource, methods=["GET"], name=heading)
    for path, (heading, description) in pages.items():
        register(path, heading, description)
    app.include_router(router)
    app.mount("/static/www", StaticFiles(directory=ROOT / "static"), name="www-static")
    return app

app = create_app()
