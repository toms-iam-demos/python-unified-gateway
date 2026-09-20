"""Verify docusign Connect signatures against the original request bytes."""

import base64
import binascii
import hashlib
import hmac
import logging
import os
import re
from typing import Iterable, Tuple

from fastapi import HTTPException

log = logging.getLogger("gateway.connect_hmac")
_SIGNATURE_HEADER = re.compile(r"x-docusign-signature-[1-9][0-9]*", re.IGNORECASE)


def require_connect_hmac(body: bytes, headers: Iterable[Tuple[str, str]]) -> None:
    """Fail closed; accept a match in any numbered signature header for rotation.

    The configured key is used as UTF-8 text, not base64-decoded. Only the
    signature is base64 encoded. Never log keys, signatures or request bodies.
    """
    secret = os.environ.get("DOCUSIGN_CONNECT_HMAC_SECRET", "")
    if not secret.strip():
        log.error("connect_hmac_rejected reason=key_not_configured")
        raise HTTPException(status_code=503, detail="Webhook verification unavailable")

    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    matched = False
    for name, value in headers:
        if not _SIGNATURE_HEADER.fullmatch(name):
            continue
        # A SHA-256 digest is exactly 44 base64 characters, including padding.
        if len(value) != 44:
            continue
        try:
            supplied = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError):
            continue
        matched |= hmac.compare_digest(expected, supplied)

    if not matched:
        log.warning("connect_hmac_rejected reason=missing_or_invalid_signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
