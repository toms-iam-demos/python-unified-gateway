# gateway/docusign_auth.py

import os
import time
from pathlib import Path
from typing import Tuple

import jwt
import requests
from dotenv import load_dotenv

# Load .env from project root once
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

DS_INTEGRATION_KEY = os.environ["DS_INTEGRATION_KEY"]
DS_USER_ID = os.environ["DS_USER_ID"]
DS_AUTH_SERVER = os.environ.get("DS_AUTH_SERVER", "account-d.docusign.com")
DS_PRIVATE_KEY_PATH = os.environ["DS_PRIVATE_KEY_PATH"]
DS_TOKEN_SCOPES = os.environ.get("DS_TOKEN_SCOPES", "signature impersonation")

# simple in-memory cache
_token_cache: dict[str, str | float | None] = {
    "access_token": None,
    "expires_at": 0.0,
}


def _load_private_key() -> str:
    key_path = Path(DS_PRIVATE_KEY_PATH).expanduser()
    return key_path.read_text(encoding="utf-8")


def _build_jwt() -> str:
    now = int(time.time())
    payload = {
        "iss": DS_INTEGRATION_KEY,
        "sub": DS_USER_ID,
        "aud": DS_AUTH_SERVER,
        "iat": now,
        "exp": now + 3600,
        "scope": DS_TOKEN_SCOPES,
    }
    private_key = _load_private_key()
    return jwt.encode(payload, private_key, algorithm="RS256")


def _exchange_for_token(assertion: str) -> Tuple[str, float]:
    url = f"https://{DS_AUTH_SERVER}/oauth/token"
    resp = requests.post(
        url,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
        timeout=15,
    )
    resp.raise_for_status()
    body = resp.json()
    access_token = body["access_token"]
    expires_in = body.get("expires_in", 3600)
    # refresh a bit early
    expires_at = time.time() + expires_in * 0.9
    return access_token, expires_at


def get_docusign_access_token() -> str:
    """
    Main entrypoint – call this anywhere in the gateway
    to get a valid DocuSign access token.
    """
    now = time.time()
    if (
        _token_cache["access_token"] is not None
        and isinstance(_token_cache["expires_at"], float)
        and now < _token_cache["expires_at"]
    ):
        return _token_cache["access_token"]  # type: ignore[return-value]

    assertion = _build_jwt()
    token, expires_at = _exchange_for_token(assertion)
    _token_cache["access_token"] = token
    _token_cache["expires_at"] = expires_at
    return token
