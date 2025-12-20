from fastapi import FastAPI

from gateway.routers import docusign, docusign_jwt_test, events, health, webhooks

app = FastAPI(title="Python Unified Gateway")

app.include_router(health.router)
app.include_router(webhooks.router)
app.include_router(events.router)
app.include_router(docusign.router)
app.include_router(docusign_jwt_test.router, prefix="/docusign")
