from fastapi import FastAPI
from gateway.routers import health, webhooks

app = FastAPI(title="Python Unified Gateway")

app.include_router(health.router)
app.include_router(webhooks.router)
