import re
from datetime import datetime, timedelta
from typing import Optional, Tuple


def parse_args(text: str) -> tuple[Optional[int], str]:
    """Deprecated: use specific duration parsers in handlers."""
    if not text:
        return None, "Без причини"
    return None, text.strip()


def parse_duration_to_datetime(duration_str: str) -> Optional[datetime]:
    """Deprecated: use seconds parser or directly pass until to API."""
    duration_str = duration_str.strip().lower()
    if duration_str in ["перманентний", "permanent", "perm"]:
        return None
    unit = duration_str[-1]
    value = int(duration_str[:-1])
    if unit == "m":
        return datetime.now() + timedelta(minutes=value)
    elif unit == "h":
        return datetime.now() + timedelta(hours=value)
    elif unit == "d":
        return datetime.now() + timedelta(days=value)
    else:
        return None


def parse_duration_to_seconds(duration_str: str) -> tuple[Optional[int], Optional[str]]:
    duration_str = duration_str.lower()
    if duration_str == "перманентний":
        return None, "назавжди"
    try:
        num = int("".join(filter(str.isdigit, duration_str)))
    except ValueError:
        return None, None
    if "m" in duration_str:
        return num * 60, f"{num} хвилин"
    elif "h" in duration_str:
        return num * 3600, f"{num} годин"
    elif "d" in duration_str:
        return num * 86400, f"{num} днів"
    return None, None

