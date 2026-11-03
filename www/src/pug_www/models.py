"""Business taxonomy and immutable example identity, independent of branding."""
from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Section(Record):
    title: str
    paragraphs: list[str] = Field(default_factory=list)

class Organization(Record):
    name: str
    logo: str | None = None

class Material(Record):
    title: str
    kind: Literal["guide", "design", "artifact", "recording", "evidence", "implementation"]
    href: str | None = None

    @field_validator("href")
    @classmethod
    def safe_url(cls, value):
        return safe_url(value)

def safe_url(value):
    if value is not None and not (value.startswith("https://") or (value.startswith("/") and not value.startswith(("//", "/\\")))):
        raise ValueError("Links require HTTPS or a same-origin path")
    return value

class Entry(Record):
    uid: UUID
    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    example_code: str | None = Field(default=None, pattern=r"^EX-\d{6}$")
    kind: Literal["enterprise-example", "integration-pattern"] = "enterprise-example"
    platforms: list[str] = Field(default_factory=list)
    business_process: str
    scenario: str
    summary: str
    industries: list[str] = Field(min_length=1)
    capabilities: list[str] = Field(min_length=1)
    organization_profile: str | None = None
    status: Literal["verified", "workbench", "preview", "planned"]
    availability: Literal["hosted", "local", "planned"] = "planned"
    updated: date
    verified: date | None = None
    experiences: dict[Literal["presentation", "workspace", "clickthrough", "video"], str] = Field(default_factory=dict)
    aliases: list[str] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    materials: list[Material] = Field(default_factory=list)

    @field_validator("experiences")
    @classmethod
    def safe_experiences(cls, values):
        for value in values.values():
            safe_url(value)
        return values

    @model_validator(mode="after")
    def registered_id(self):
        if self.example_code and self.id != self.example_code.lower():
            raise ValueError("Registered examples use their stable EX code in canonical URLs")
        return self

class PresentationBinding(Record):
    """Private presentation files; these do not grant provider access."""
    template: str | None = None
    html_file: str | None = None
    assets: dict[str, str] = Field(default_factory=dict)
    runtime_namespace: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    reference_sessions: list[UUID] = Field(default_factory=list)

class Profile(Record):
    schema_version: Literal[2] = 2
    name: str = "Python Unified Gateway"
    tagline: str = "Every agreement. Every connection."
    entries: list[Entry] = Field(default_factory=list)
    organizations: dict[str, Organization] = Field(default_factory=dict)
    assets: dict[str, str] = Field(default_factory=dict)
    presentations: dict[str, PresentationBinding] = Field(default_factory=dict)

    @model_validator(mode="after")
    def identity_and_references(self):
        ids, uids, names = set(), set(), set()
        for entry in self.entries:
            if entry.id in ids or entry.uid in uids:
                raise ValueError("Example IDs and UUIDs must be unique")
            ids.add(entry.id); uids.add(entry.uid)
            for name in [entry.id, *entry.aliases]:
                if name.casefold() in names:
                    raise ValueError("Example aliases must be globally unique")
                names.add(name.casefold())
            if entry.organization_profile and entry.organization_profile not in self.organizations:
                raise ValueError("Unknown organization profile")
        if not set(self.presentations).issubset(ids):
            raise ValueError("Presentation binding must belong to a catalog example")
        return self
