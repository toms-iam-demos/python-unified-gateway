"""Validated content shared by catalog pages, filters and navigation."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Section(BaseModel):
    title: str
    paragraphs: list[str] = Field(default_factory=list)

class Entry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str
    organization: str
    summary: str
    category: str
    capability: str
    status: Literal["verified", "workbench", "preview", "planned"]
    updated: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    verified: str | None = None
    launch_url: str | None = None
    logo: str | None = None
    formats: list[Literal["live", "video", "clickthrough"]] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)

    @field_validator("launch_url")
    @classmethod
    def safe_launch(cls, value):
        if value is not None and not (value.startswith("https://") or (value.startswith("/") and not value.startswith("//"))):
            raise ValueError("Launch links require HTTPS or a same-origin path")
        return value

class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = "Python Unified Gateway"
    tagline: str = "Every agreement. Every connection."
    entries: list[Entry] = Field(default_factory=list)
    assets: dict[str, str] = Field(default_factory=dict)

    @field_validator("entries")
    @classmethod
    def unique_ids(cls, entries):
        if len({e.id for e in entries}) != len(entries):
            raise ValueError("Catalog IDs must be unique")
        return entries
