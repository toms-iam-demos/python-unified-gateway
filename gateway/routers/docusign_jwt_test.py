from __future__ import annotations

import os
import time
import json
from typing import Any, Dict

import jwt  # PyJWT
import requests
from fastapi import APIRouter, HTTPException

router = APIRouter()


def _require_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise HTTPException(status_code=500, detail=f"Missing required env var: {name}")
    return v


def _read_private_key(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Private key file not found: {path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read private key at {path}: {e}")


def _safe_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return text


@router.get("/jwt-test")
def jwt_test() -> Dict[str, Any]:
    """
    Proves JWT auth works by:
      1) minting a JWT assertion (RS256)
      2) exchanging it for an access token at /oauth/token
      3) calling /oauth/userinfo using that access token
    """
    ds_client_id = _require_env("DS_CLIENT_ID")
    ds_user_guid = _require_env("DS_IMPERSONATED_USER_GUID")
    ds_auth_server = _require_env("DS_AUTH_SERVER")  # e.g. account-d.docusign.com
    ds_private_key_path = _require_env("DS_PRIVATE_KEY_PATH")

    private_key_pem = _read_private_key(ds_private_key_path)

    now = int(time.time())
    payload = {
        "iss": ds_client_id,
        "sub": ds_user_guid,
        "aud": ds_auth_server,
        "iat": now,
        "exp": now + 3600,
        "scope": "signature impersonation",
    }

    try:
        assertion = jwt.encode(payload, private_key_pem, algorithm="RS256")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JWT signing failed: {e}")

    token_url = f"https://{ds_auth_server}/oauth/token"
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    }

    try:
        token_resp = requests.post(token_url, data=data, timeout=20)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Token request to DocuSign failed: {e}")

    if token_resp.status_code != 200:
        raise HTTPException(
            status_code=token_resp.status_code,
            detail={
                "step": "oauth_token",
                "token_url": token_url,
                "status_code": token_resp.status_code,
                "body": _safe_json(token_resp.text),
            },
        )

    token_json = token_resp.json()
    access_token = token_json.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=500,
            detail={"step": "oauth_token", "error": "No access_token in response", "body": token_json},
        )

    userinfo_url = f"https://{ds_auth_server}/oauth/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        ui_resp = requests.get(userinfo_url, headers=headers, timeout=20)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Userinfo request to DocuSign failed: {e}")

    if ui_resp.status_code != 200:
        raise HTTPException(
            status_code=ui_resp.status_code,
            detail={
                "step": "oauth_userinfo",
                "userinfo_url": userinfo_url,
                "status_code": ui_resp.status_code,
                "body": _safe_json(ui_resp.text),
            },
        )

    return {
        "ok": True,
        "docusign_userinfo": ui_resp.json(),
        "token_meta": {
            "token_type": token_json.get("token_type"),
            "expires_in": token_json.get("expires_in"),
            "scope": token_json.get("scope"),
        },
    }
