from aiogram.filters import BaseFilter
from aiogram.types import Message

from config import settings


def load_begger_list(path: str) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        return []


ANTI_BEGGER_LIST = load_begger_list(settings.ANTI_BEGGER_FILE)


class AntiBegger(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        text = (message.text or "").lower()
        if not text:
            return False
        return any(begger in text for begger in ANTI_BEGGER_LIST)

