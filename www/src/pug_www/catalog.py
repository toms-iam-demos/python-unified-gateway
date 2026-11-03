"""Load one profile and validate its business vocabulary against the registry."""
import json
from pathlib import Path
from .models import Profile

def load_profile(path: Path | None = None) -> Profile:
    root = Path(__file__).parent
    profile = Profile.model_validate_json((path or root / "catalog.json").read_text())
    taxonomy = json.loads((root / "taxonomy.json").read_text())
    for entry in profile.entries:
        if entry.business_process not in taxonomy["business_processes"]:
            raise ValueError("Unknown business process")
        if not set(entry.industries).issubset(taxonomy["industries"]):
            raise ValueError("Unknown industry")
        if not set(entry.capabilities).issubset(taxonomy["capabilities"]):
            raise ValueError("Unknown capability")
    return profile
