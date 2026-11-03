"""Read-only Workflow Builder adapter. No trigger, cancel or delete operations."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from uuid import UUID

import jwt
import requests
from fastapi import HTTPException

from gateway.observability import span

TOKEN_SCOPES = "signature impersonation aow_manage"
_lock = threading.Lock()
_cache: dict = {}


def fail(status: int, code: str, message: str, headers=None):
    raise HTTPException(status_code=status, detail={"code": code, "message": message}, headers=headers)


def configuration():
    names = ("DS_CLIENT_ID", "DS_IMPERSONATED_USER_GUID", "DS_PRIVATE_KEY_PATH", "DS_WORKFLOW_ACCOUNT_ID")
    values = {name: os.getenv(name, "").strip() for name in names}
    if not all(values.values()):
        fail(503, "workflow_not_configured", "Workflow Builder server configuration is incomplete.")
    if os.getenv("DS_AUTH_SERVER", "") != "account-d.docusign.com":
        fail(503, "sandbox_required", "This proof of concept requires the docusign sandbox.")
    try:
        values["DS_WORKFLOW_ACCOUNT_ID"] = str(UUID(values["DS_WORKFLOW_ACCOUNT_ID"]))
    except ValueError:
        fail(503, "workflow_not_configured", "Workflow Builder account configuration is invalid.")
    return values


def access_token(config):
    key = tuple(config.items())
    with _lock:
        if _cache.get("key") == key and _cache.get("expires_at", 0) > time.monotonic():
            return _cache["token"]
        try:
            pem = Path(config["DS_PRIVATE_KEY_PATH"]).read_text()
            now = int(time.time())
            assertion = jwt.encode({
                "iss": config["DS_CLIENT_ID"], "sub": config["DS_IMPERSONATED_USER_GUID"],
                "aud": "account-d.docusign.com", "iat": now, "exp": now + 300,
                "scope": TOKEN_SCOPES,
            }, pem, algorithm="RS256")
        except Exception:
            fail(503, "workflow_auth_configuration", "The server cannot prepare workflow authentication.")
        try:
            with span("docusign workflow OAuth"):
                r = requests.post("https://account-d.docusign.com/oauth/token", data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion,
                }, timeout=(5, 20), allow_redirects=False)
        except requests.Timeout:
            fail(504, "provider_timeout", "docusign authentication timed out.")
        except requests.RequestException:
            fail(502, "provider_unavailable", "docusign authentication could not be reached.")
        try:
            body = r.json()
        except ValueError:
            fail(502, "invalid_provider_response", "docusign returned an unexpected authentication response.")
        if not isinstance(body, dict):
            fail(502, "invalid_provider_response", "docusign returned an unexpected authentication response.")
        if r.status_code != 200:
            if body.get("error") == "consent_required":
                fail(503, "docusign_consent_required", "Grant this integration signature, impersonation and aow_manage consent for the configured sandbox user.")
            fail(502, "provider_auth_failed", "docusign rejected the server authentication request.")
        token = body.get("access_token")
        if not isinstance(token, str) or not token:
            fail(502, "invalid_provider_response", "docusign did not return a usable access token.")
        try:
            lifetime = min(float(body.get("expires_in", 3600)), 3600)
        except (ValueError, TypeError):
            fail(502, "invalid_provider_response", "docusign returned an invalid token lifetime.")
        _cache.update(key=key, token=token, expires_at=time.monotonic() + max(0, lifetime - 60))
        return token


def get_json(suffix: str):
    config = configuration()
    token = access_token(config)
    url = "https://api-d.docusign.com/v1/accounts/" + config["DS_WORKFLOW_ACCOUNT_ID"] + "/workflows" + suffix
    try:
        with span("docusign Workflow Builder GET"):
            r = requests.get(url, headers={"Authorization": "Bearer " + token}, timeout=(5, 20), allow_redirects=False)
    except requests.Timeout:
        fail(504, "provider_timeout", "docusign Workflow Builder timed out.")
    except requests.RequestException:
        fail(502, "provider_unavailable", "docusign Workflow Builder could not be reached.")
    if r.status_code == 401:
        with _lock:
            _cache.clear()
        fail(502, "provider_auth_failed", "docusign rejected the server token. A subsequent request will refresh it.")
    if r.status_code == 403:
        fail(403, "provider_access_denied", "The configured docusign user cannot access this workflow resource.")
    if r.status_code == 404:
        fail(404, "workflow_resource_not_found", "The resource was not found or is unavailable to the configured account and user.")
    if r.status_code == 429:
        retry = r.headers.get("Retry-After", "")
        headers = {"Retry-After": retry} if retry.isdigit() and len(retry) < 10 else None
        fail(429, "provider_rate_limited", "docusign rate-limited this request. Retry later.", headers)
    if r.status_code != 200:
        fail(502, "provider_error", "docusign returned an unsuccessful workflow response.")
    try:
        body = r.json()
    except ValueError:
        fail(502, "invalid_provider_response", "docusign returned non-JSON workflow data.")
    if not isinstance(body, dict):
        fail(502, "invalid_provider_response", "docusign returned an unexpected workflow structure.")
    return body
