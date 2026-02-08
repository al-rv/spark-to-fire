"""
Spark to Fire – Business logic: decay rule and state transitions.
All mutations persist immediately via storage.save_data.
"""
import uuid
from datetime import datetime, timezone

from storage import load_data, save_data

DECAY_DAYS = 7
ITEM_TYPES = ("tutorial", "course", "book", "article", "project", "idea", "other")
STATUSES = ("envisioned", "in_progress", "discarded", "completed")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_decay(data: dict) -> None:
    """
    For each item with status in_progress: if last_accessed_at is missing
    or older than DECAY_DAYS days, set status=discarded and discarded_at=now.
    Then save.
    """
    now = datetime.now(timezone.utc)
    changed = False
    for item in data.get("items", []):
        if item.get("status") != "in_progress":
            continue
        la = item.get("last_accessed_at")
        if not la:
            item["status"] = "discarded"
            item["discarded_at"] = _now_iso()
            changed = True
            continue
        try:
            dt = datetime.fromisoformat(la.replace("Z", "+00:00"))
            if (now - dt).days >= DECAY_DAYS:
                item["status"] = "discarded"
                item["discarded_at"] = _now_iso()
                changed = True
        except (ValueError, TypeError):
            item["status"] = "discarded"
            item["discarded_at"] = _now_iso()
            changed = True
    if changed:
        save_data(data)


def create_item(data: dict, title: str, type_key: str) -> dict:
    """Append new item (status=envisioned, date_added=now); save; return the new item."""
    if type_key not in ITEM_TYPES:
        type_key = "other"
    item = {
        "id": str(uuid.uuid4()),
        "title": (title or "").strip() or "Untitled",
        "type": type_key,
        "status": "envisioned",
        "date_added": _now_iso(),
        "moved_to_in_progress_at": None,
        "last_accessed_at": None,
        "discarded_at": None,
        "completed_at": None,
        "takeaways": None,
        "learning_notes": None,
    }
    data.setdefault("items", []).append(item)
    save_data(data)
    return item


def _find_item(data: dict, item_id: str):
    for item in data.get("items", []):
        if item.get("id") == item_id:
            return item
    return None


def move_to_in_progress(data: dict, item_id: str) -> bool:
    now = _now_iso()
    item = _find_item(data, item_id)
    if not item:
        return False
    item["status"] = "in_progress"
    item["moved_to_in_progress_at"] = now
    item["last_accessed_at"] = now
    save_data(data)
    return True


def move_to_discarded(data: dict, item_id: str) -> bool:
    item = _find_item(data, item_id)
    if not item:
        return False
    item["status"] = "discarded"
    item["discarded_at"] = _now_iso()
    save_data(data)
    return True


def move_to_completed(data: dict, item_id: str) -> bool:
    item = _find_item(data, item_id)
    if not item:
        return False
    item["status"] = "completed"
    item["completed_at"] = _now_iso()
    save_data(data)
    return True


def update_last_accessed(data: dict, item_id: str) -> bool:
    item = _find_item(data, item_id)
    if not item or item.get("status") != "in_progress":
        return False
    item["last_accessed_at"] = _now_iso()
    save_data(data)
    return True


def update_item(data: dict, item_id: str, **fields) -> bool:
    """Update allowed fields (e.g. takeaways, learning_notes); save."""
    item = _find_item(data, item_id)
    if not item:
        return False
    allowed = {"takeaways", "learning_notes", "title", "type"}
    for k, v in fields.items():
        if k in allowed:
            item[k] = v
    save_data(data)
    return True


def delete_item(data: dict, item_id: str) -> bool:
    """Remove item from data and save. Returns True if removed."""
    items = data.get("items", [])
    for i, item in enumerate(items):
        if item.get("id") == item_id:
            items.pop(i)
            save_data(data)
            return True
    return False
