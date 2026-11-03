"""Use an existing server-held bcrypt password file, failing closed."""
import base64
import secrets
import bcrypt
from fastapi import HTTPException
from .settings import Settings

def authenticate(header: str, settings: Settings) -> str:
    challenge = {"WWW-Authenticate": 'Basic realm="PUG"'}
    if not settings.htpasswd_file:
        raise HTTPException(503, "Operator authentication is not configured")
    try:
        entries = [line.split(":", 1) for line in settings.htpasswd_file.read_text().splitlines() if line.strip()]
        if not entries or any(len(row) != 2 or not row[1].startswith(("$2a$", "$2b$", "$2y$")) for row in entries):
            raise OSError()
    except OSError:
        raise HTTPException(503, "Operator authentication unavailable") from None
    try:
        scheme, value = header.split(" ", 1)
        if scheme.lower() != "basic":
            raise ValueError()
        user, password = base64.b64decode(value, validate=True).decode().split(":", 1)
        selected = next((hashed for name, hashed in entries if secrets.compare_digest(name.encode(), user.encode())), None)
        raw = password.encode()
        valid = len(raw) <= 72 and bcrypt.checkpw(raw, (selected or entries[0][1]).encode())
        if selected is None or not valid:
            raise ValueError()
        return user
    except (ValueError, UnicodeError):
        raise HTTPException(401, "PUG operator login required", headers=challenge) from None
