from fastapi import APIRouter, Request

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/docusign")
async def docusign_webhook(request: Request):
    # For now just echo that we got it – we’ll evolve this
    body = await request.body()
    # Later: parse XML, store in DB, trigger Maestro, Navigator, etc.
    return {"status": "received", "length": len(body)}
