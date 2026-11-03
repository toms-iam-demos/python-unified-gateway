"""One versioned profile supplies the site; no JavaScript content fork."""
from pathlib import Path
from .models import Profile

def load_profile(path: Path | None = None) -> Profile:
    return Profile.model_validate_json((path or Path(__file__).with_name("catalog.json")).read_text())
