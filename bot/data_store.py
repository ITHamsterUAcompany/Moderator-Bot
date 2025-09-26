import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import settings


@dataclass
class HistoryEntry:
    type: str
    reason: str
    date: str
    until: Optional[str] = None


class DataStore:
    """JSON-backed store with context-managed save and typed helpers."""

    def __init__(self, file_path: str = settings.DATA_FILE) -> None:
        self.file_path = file_path
        self.data: Dict[str, Any] = {
            "muted_users": {},
            "warnings": {},
            "karma": {},
            "history": {},
            "banned_users": [],
        }
        self._load_from_disk()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.save()
        return False

    def _load_from_disk(self) -> None:
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.data.update(loaded)
        except Exception:
            pass

    def save(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    # History
    def append_history(self, user_id: int, entry: HistoryEntry) -> None:
        uid = str(user_id)
        self.data.setdefault("history", {}).setdefault(uid, []).append(asdict(entry))
        self.save()

    def pop_last_warn(self, user_id: int) -> bool:
        uid = str(user_id)
        history = self.data.get("history", {}).get(uid, [])
        for i in range(len(history) - 1, -1, -1):
            if history[i].get("type") == "warn":
                history.pop(i)
                self.save()
                return True
        return False

    def get_history(self, user_id: int) -> List[HistoryEntry]:
        raw = self.data.get("history", {}).get(str(user_id), [])
        result: List[HistoryEntry] = []
        for item in raw:
            result.append(
                HistoryEntry(
                    type=item.get("type", ""),
                    reason=item.get("reason", ""),
                    date=item.get("date", ""),
                    until=item.get("until"),
                )
            )
        return result

    # Karma
    def get_karma(self, user_id: int, is_admin: bool = False) -> int:
        uid = str(user_id)
        if uid not in self.data.get("karma", {}):
            self.data.setdefault("karma", {})[uid] = 1000 if is_admin else 0
            self.save()
        return int(self.data["karma"][uid])

    def set_karma(self, user_id: int, value: int) -> int:
        uid = str(user_id)
        self.data.setdefault("karma", {})[uid] = value
        self.save()
        return value

    def add_karma(self, user_id: int, delta: int) -> int:
        current = self.get_karma(user_id)
        new_val = max(-1000, min(1000, current + delta))
        return self.set_karma(user_id, new_val)


