from fastapi import FastAPI
from gateway.routers import health, webhooks, docusign

app = FastAPI(title="Python Unified Gateway")

app.include_router(health.router)
app.include_router(webhooks.router)
app.include_router(docusign.router)
