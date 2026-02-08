"""
Spark to Fire – JSON storage for data.json.
Load/save with atomic write; create file if missing.
"""
import json
import os

DATA_FILE = "data.json"


def load_data() -> dict:
    """Read data.json; if missing or invalid, return {"items": []}."""
    if not os.path.exists(DATA_FILE):
        return {"items": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "items" not in data:
            return {"items": []}
        if not isinstance(data["items"], list):
            return {"items": []}
        return data
    except (json.JSONDecodeError, OSError):
        return {"items": []}


def save_data(data: dict) -> None:
    """Write data to data.json (atomic: temp file then replace)."""
    if not isinstance(data, dict) or "items" not in data:
        raise ValueError("data must be a dict with 'items' key")
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)
