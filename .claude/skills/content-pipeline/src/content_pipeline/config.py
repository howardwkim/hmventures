import json
from pathlib import Path

CONFIG_PATH = Path("~/.content-pipeline/config.json").expanduser()


def load() -> dict:
    """Read the operator config if present, else {}. Never raises on a
    missing, unreadable, or malformed file - the pipeline runs with empty
    defaults. Catches OSError (missing/permission/IO) and ValueError
    (invalid JSON)."""
    try:
        return json.loads(CONFIG_PATH.read_text())
    except (OSError, ValueError):
        return {}


def brand_context() -> str:
    return load().get("brand_context", "")
