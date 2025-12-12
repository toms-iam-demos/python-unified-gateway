# gateway/routers/docusign_ping.py

from fastapi import APIRouter, HTTPException
import requests

from gateway.docusign_auth import (
    get_docusign_access_token,
    DS_AUTH_SERVER,
)

router = APIRouter(prefix="/docusign", tags=["docusign"])


@router.get("/ping")
def docusign_ping():
    """
    Smoke test:
    - Uses JWT helper to get a token
    - Calls DocuSign /oauth/userinfo
    """
    token = get_docusign_access_token()

    url = f"https://{DS_AUTH_SERVER}/oauth/userinfo"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return {
        "status": "ok",
        "auth_server": DS_AUTH_SERVER,
        "userinfo": resp.json(),
    }
