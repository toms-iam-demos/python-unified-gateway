"""Environment configuration; credentials are never catalog content."""
from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class Settings:
    require_auth: bool = True
    htpasswd_file: Path | None = None
    profile_file: Path | None = None
    asset_directory: Path | None = None
    presentation_directory: Path | None = None
    runtime_origin: str | None = None
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "testserver")

    @classmethod
    def from_env(cls):
        def path(name):
            value = os.getenv(name)
            return Path(value) if value else None
        return cls(
            require_auth=os.getenv("WWW_REQUIRE_AUTH", "true").lower() != "false",
            htpasswd_file=path("WWW_HTPASSWD_FILE"),
            profile_file=path("WWW_PROFILE_FILE"),
            asset_directory=path("WWW_ASSET_DIRECTORY"),
            presentation_directory=path("WWW_PRESENTATION_DIRECTORY"),
            runtime_origin=os.getenv("WWW_RUNTIME_ORIGIN"),
            allowed_hosts=tuple(h.strip() for h in os.getenv("WWW_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()),
        )
