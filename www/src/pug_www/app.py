"""Repository website with stable example routes and isolated presentations."""
from pathlib import Path
import mimetypes
import json
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.concurrency import run_in_threadpool
from .catalog import load_profile
from .navigation import GROUPS
from .security import authenticate
from .settings import Settings
from . import presentations

ROOT = Path(__file__).parent
mimetypes.add_type("font/woff2", ".woff2")

def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    profile = load_profile(settings.profile_file)
    app_center = json.loads((ROOT / "app-center.json").read_text())
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
    def organization(entry):
        return profile.organizations.get(entry.organization_profile)
    def page(request, template, **context):
        return templates.TemplateResponse(request=request, name=template, context={"profile": profile, "navigation": GROUPS, "organization": organization, **context})
    def resolve(value):
        value = value.casefold()
        entry = next((entry for entry in profile.entries if value in {entry.id, *[alias.casefold() for alias in entry.aliases]}), None)
        if entry is None:
            raise HTTPException(404, "Example not found")
        return entry
    def binding(example_id):
        value = profile.presentations.get(resolve(example_id).id)
        if value is None:
            raise HTTPException(404, "Presentation not configured for this example")
        return value

    @router.get("/")
    async def home(request: Request):
        return page(request, "home.html", title="PUG", entries=profile.entries[:3])

    @router.get("/catalog")
    @router.get("/demos")
    async def catalog(request: Request):
        area = request.query_params.get("area")
        if area == "overview":
            return RedirectResponse("/", status_code=303)
        if area == "extensions":
            stripe = next((entry for entry in profile.entries if entry.id == "stripe-consulting-deposit"), None)
            return page(request, "app-center.html", title="App Center", apps=app_center, stripe=stripe)
        if area == "workups":
            return page(request, "invitations.html", title="Invitations", entries=sorted(profile.entries, key=lambda entry: entry.scenario))
        entries = sorted(profile.entries, key=lambda entry: (entry.business_process, entry.scenario))
        facets = {
            "process": sorted({entry.business_process for entry in entries}),
            "industry": sorted({industry for entry in entries for industry in entry.industries}),
            "capability": sorted({capability for entry in entries for capability in entry.capabilities}),
            "organization": sorted({organization(entry).name for entry in entries if organization(entry)}),
        }
        groups = {process: [entry for entry in entries if entry.business_process == process] for process in facets["process"]}
        return page(request, "catalog.html", title="Demo catalog", entries=entries, facets=facets, groups=groups)

    @router.get("/catalog/{slug}")
    async def legacy_detail(request: Request, slug: str):
        entry = resolve(slug)
        suffix = "?" + request.url.query if request.url.query else ""
        return RedirectResponse(f"/demos/{entry.id}/" + suffix, status_code=307)

    @router.get("/demos/data-studio")
    async def data_studio(request: Request):
        return page(request, "resource.html", title="Data Studio", description="A proposed shared capability for configuring, generating and versioning demonstration datasets. No dataset generator is enabled in this preview.")

    @router.get("/demos/{example_id}/")
    async def detail(request: Request, example_id: str):
        entry = resolve(example_id)
        if example_id != entry.id:
            return RedirectResponse(f"/demos/{entry.id}/", status_code=307)
        return page(request, "detail.html", title=entry.scenario, entry=entry, presentation=entry.id in profile.presentations)

    @router.get("/demos/{example_id}/runs/")
    @router.get("/demos/{example_id}/materials/")
    @router.get("/demos/{example_id}/implementation/")
    async def example_section(request: Request, example_id: str):
        entry = resolve(example_id)
        section = request.url.path.rstrip("/").rsplit("/", 1)[-1]
        value = profile.presentations.get(entry.id)
        materials = [material for material in entry.materials if (material.kind == "implementation") == (section == "implementation")]
        return page(request, "example-section.html", title=section.title(), entry=entry, materials=materials, references=value.reference_sessions if value else [])

    @router.get("/demos/{example_id}/presentation/")
    async def presentation(example_id: str):
        entry = resolve(example_id)
        content = presentations.presentation_html(settings, binding(entry.id), entry.id, entry.scenario, organization(entry).name if organization(entry) else None)
        return HTMLResponse(content, headers={"X-PUG-Preview-Commands": "disabled"})

    @router.get("/demos/{example_id}/assets/{name}")
    async def presentation_asset(example_id: str, name: str):
        entry = resolve(example_id); value = binding(entry.id)
        bundled = presentations.BUNDLED / name
        if value.template and name in {"presentation.js", "presentation.css", "provider-journey.js", "provider-presenter.js", "crm-journey.js", "iris-challenge.js"} and bundled.is_file():
            path = bundled
        else:
            relative = value.assets.get(name)
            if not relative:
                raise HTTPException(404, "Presentation asset not found")
            path = presentations.owned_file(settings.presentation_directory, relative)
        if path.suffix in presentations.TEXT_TYPES:
            return Response(presentations.rewrite(path.read_text(), entry.id, value.runtime_namespace), media_type=presentations.TEXT_TYPES[path.suffix])
        if path.suffix not in presentations.MEDIA_TYPES:
            raise HTTPException(404, "Asset format is not permitted")
        return FileResponse(path, media_type=presentations.MEDIA_TYPES[path.suffix])

    @router.get("/api/demos/{example_id}/runtime/{path:path}")
    async def runtime_read(example_id: str, path: str):
        entry = resolve(example_id)
        content, content_type = await presentations.read_runtime(settings, binding(entry.id), entry.id, path)
        return Response(content, media_type=content_type)

    @router.post("/api/demos/{example_id}/runtime/{path:path}")
    async def runtime_command(example_id: str, path: str):
        resolve(example_id)
        raise HTTPException(403, "Provider commands are disabled in this migration preview. Existing run evidence remains readable.")

    @router.get("/api/v1/www/catalog")
    async def catalog_data():
        return {"schema_version": 2, "entries": [entry.model_dump(mode="json") for entry in profile.entries], "organizations": {key: value.model_dump() for key, value in profile.organizations.items()}}

    @router.get("/brand/{name}")
    async def brand(name: str):
        relative = profile.assets.get(name)
        if not relative or not settings.asset_directory:
            raise HTTPException(404, "Asset not found")
        base = settings.asset_directory.resolve(); path = (base / relative).resolve()
        if not path.is_relative_to(base) or path.suffix.lower() not in {".svg", ".png", ".jpg", ".jpeg", ".webp", ".woff2"} or not path.is_file():
            raise HTTPException(404, "Asset not found")
        return FileResponse(path)

    pages = {
        "/build": ("Build", "Inspect provider contracts and integration capabilities. Capabilities describe what a system can do; enterprise examples describe a business process and scenario."),
        "/resources": ("Resources", "Guides, design documents, implementation material and evidence belong to their example. Run-generated artifacts retain their original run association."),
        "/workspaces/agents": ("Agents", "Development workups for agreement agents. This is a capability workspace, not an enterprise example or connected agent runtime."),
        "/workspaces/mcp": ("MCP", "Your owner-branded capability workspace. Its identity is separate from the business scenarios that use its tools."),
        "/workspaces/ham": ("HAM", "The enterprise emulation workspace. CRM, ERP and HRIS are integration capabilities, while their business scenarios belong in Demos."),
    }
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
