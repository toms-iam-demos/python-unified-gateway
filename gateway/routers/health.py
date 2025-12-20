from fastapi import APIRouter

from gateway.db.init_db import ensure_schema

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    return {"status": "ok", "source": "python-unified-gateway"}


@router.get("/ready")
async def readiness_check():
    """
    Readiness should never crash the process.
    It reports whether persistence is currently available.
    """
    s = ensure_schema()
    return {
        "ready": bool(s.ready),
        "db": {"enabled": s.enabled, "mode": s.mode, "detail": s.detail},
    }
