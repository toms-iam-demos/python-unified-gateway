"""Preserve an existing presentation behind a canonical example route.

Source files and recordings stay outside the public package. The review bridge is
read-only: all provider commands fail closed, including while previewing anonymously.
"""
from pathlib import Path
import re
import json
from html import escape
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException

ALLOWED_RUNTIME = re.compile(r"^(?:replay|sessions/[0-9a-f-]{36}(?:/(?:evidence|iris/evidence|iris/documents/[a-z-]+\.pdf|iris/attempts/[0-9a-f-]{36}))?)$")
BUNDLED = Path(__file__).parent / "experiences" / "presentation"
TEMPLATES = {"provider": "provider.html", "service-agreement": "service-agreement.html", "crm": "crm.html"}
TEXT_TYPES = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}
MEDIA_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".woff2": "font/woff2"}

def owned_file(directory, relative):
    if directory is None:
        raise HTTPException(503, "Presentation files are not configured")
    base = directory.resolve(); path = (base / relative).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise HTTPException(404, "Presentation file not found")
    return path

def rewrite(text, example_id, namespace):
    root = f"/demos/{example_id}"
    text = text.replace("/assets/summit/", root + "/assets/")
    text = text.replace("/assets/e6e64315362ccf4b.woff2", root + "/assets/presentation-font.woff2")
    text = text.replace("/api/summit", f"/api/demos/{example_id}/runtime")
    text = text.replace("location.pathname.split('/')[2]||'legacy'", "document.body.dataset.runtimeNamespace||'legacy'")
    text = text.replace("/summit/" + namespace, root + "/presentation/")
    text = text.replace('href="/#/examples"', f'href="{root}/"')
    for old, new in [("Summit session", "Run"), ("No summit run", "No run"), ("current summit run", "current run"), ("fresh summit run", "fresh run"), ("AI SUMMIT / THE LIVE CHALLENGE", "EXAMPLE / PRESENTATION")]:
        text = text.replace(old, new)
    return text.replace("\u2014", " - ")

def presentation_html(settings, binding, example_id, scenario=None, organization=None):
    if binding.template:
        filename = TEMPLATES.get(binding.template)
        if not filename:
            raise HTTPException(404, "Presentation template not found")
        text = (BUNDLED / filename).read_text()
    elif binding.html_file:
        text = owned_file(settings.presentation_directory, binding.html_file).read_text()
    else:
        raise HTTPException(404, "Presentation not configured")
    text = rewrite(text, example_id, binding.runtime_namespace)
    if scenario:
        text = re.sub(r"<title>.*?</title>", "<title>" + escape(scenario) + " | " + example_id.upper() + "</title>", text, count=1, flags=re.S)
        label = escape((organization + " / " if organization else "") + example_id.upper())
        text = re.sub(r'(<span class="summit-label">).*?(</span>)', lambda match: match.group(1) + label + match.group(2), text, count=1, flags=re.S)
    frontend_namespace = "provider" if binding.template == "provider" else binding.runtime_namespace
    if binding.template == "provider":
        text = text.replace("/summit/provider", f"/demos/{example_id}/presentation/")
    if binding.reference_sessions:
        text = text.replace('data-reference-session=""', 'data-reference-session="' + str(binding.reference_sessions[0]) + '"', 1)
    marker = f'data-runtime-namespace="{frontend_namespace}" '
    if "<body " in text:
        text = text.replace("<body ", "<body " + marker, 1)
    else:
        text = text.replace("<body>", "<body " + marker + ">", 1)
    if '<div class="operator-notes"' in text:
        text = text.replace('<div class="operator-notes"', '<p class="footnote">Migration preview: preserved run evidence is available. Provider commands are disabled.</p><div class="operator-notes"', 1)
    # Existing execution evidence remains unchanged; visible shell labels use demo terminology.
    text = text.replace("Synthetic, nonbinding agreements. Real Docusign execution.", "Demonstration agreements. Docusign execution evidence.")
    return text

async def read_runtime(settings, binding, example_id, path):
    if not settings.runtime_origin or not ALLOWED_RUNTIME.fullmatch(path):
        raise HTTPException(404, "Runtime read is not available")
    origin = urlparse(settings.runtime_origin)
    if origin.hostname not in {"127.0.0.1", "localhost"} or origin.scheme != "http":
        raise HTTPException(503, "Migration runtime must use an explicitly configured loopback service")
    try:
        async with httpx.AsyncClient(base_url=settings.runtime_origin, timeout=30, follow_redirects=False, trust_env=False) as client:
            if path.startswith("sessions/"):
                sid = path.split("/")[1]
                record = await client.get("/api/summit/sessions/" + sid)
                if record.status_code != 200:
                    raise HTTPException(404, "Run not found")
                namespace = record.json().get("namespace")
                if namespace != binding.runtime_namespace and sid not in {str(value) for value in binding.reference_sessions}:
                    raise HTTPException(404, "Run does not belong to this example")
            result = await client.get("/api/summit/" + path)
    except httpx.RequestError:
        raise HTTPException(503, "Existing example runtime is unavailable") from None
    if result.status_code != 200:
        raise HTTPException(result.status_code if result.status_code in {403, 404} else 502, "Runtime read failed")
    content_type = result.headers.get("content-type", "application/octet-stream")
    if "json" in content_type:
        def links(value):
            if isinstance(value, dict):
                return {("provider" if key == binding.runtime_namespace and binding.template == "provider" else key): ("provider" if key == "namespace" and item == binding.runtime_namespace and binding.template == "provider" else links(item)) for key, item in value.items()}
            if isinstance(value, list):
                return [links(item) for item in value]
            if isinstance(value, str) and value.startswith(("/api/summit/", "/assets/summit/")):
                return rewrite(value, example_id, binding.runtime_namespace)
            return value
        return json.dumps(links(result.json())).encode(), content_type
    return result.content, content_type
