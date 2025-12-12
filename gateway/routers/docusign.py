from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/docusign",
    tags=["docusign"],
)


class PingResponse(BaseModel):
    status: str
    message: str


@router.get("/ping", response_model=PingResponse)
async def docusign_ping() -> PingResponse:
    """
    Simple health-check for the DocuSign integration.

    For now this just proves the gateway + router wiring works.
    Later we can extend it to:
      - Perform a JWT grant
      - Hit /oauth/userinfo
      - Return account / org details
    """
    return PingResponse(
        status="ok",
        message="python-unified-gateway /docusign/ping is online",
    )
