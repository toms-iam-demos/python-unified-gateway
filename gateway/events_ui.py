"""Read-only event browser. /events/* remains behind operator ingress authentication."""
from pathlib import Path
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse, JSONResponse
from gateway.event_snapshot import SnapshotCache, SnapshotUnavailable
from gateway.routers.events import latest_events

router = APIRouter(include_in_schema=False)
ROOT = Path(__file__).parent / "event_explorer"
snapshot = SnapshotCache()
POLICY = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
}

@router.get('/events/ui/snapshot')
async def event_snapshot(refresh: bool = Query(False)):
    try:
        value = await snapshot.get(latest_events, refresh=refresh)
    except SnapshotUnavailable as error:
        return JSONResponse({"ready": False, "detail": str(error)}, status_code=503, headers=POLICY)
    return JSONResponse(value, headers=POLICY)

@router.get('/events/ui')
async def event_explorer():
    return FileResponse(ROOT / 'index.html', media_type='text/html', headers=POLICY)

@router.get('/events/ui/assets/app.js')
async def event_explorer_script():
    return FileResponse(ROOT / 'app.js', media_type='text/javascript', headers=POLICY)

@router.get('/events/ui/assets/app.css')
async def event_explorer_style():
    return FileResponse(ROOT / 'app.css', media_type='text/css', headers=POLICY)
