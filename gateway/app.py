from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from gateway.routers import docusign, docusign_jwt_test, events, health, webhooks

app = FastAPI(title="Python Unified Gateway")

# Static assets (monitor UI JS)
app.mount("/static", StaticFiles(directory="gateway/static"), name="static")

app.include_router(health.router)
app.include_router(webhooks.router)
app.include_router(events.router)
app.include_router(docusign.router)
app.include_router(docusign_jwt_test.router, prefix="/docusign")
