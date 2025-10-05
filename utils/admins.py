import time
from typing import Dict, List

from aiogram import Bot


_cache: Dict[int, tuple[float, List[int]]] = {}
_TTL_SECONDS = 60


async def get_admin_ids(bot: Bot, chat_id: int) -> List[int]:
    now = time.time()
    if chat_id in _cache:
        ts, ids = _cache[chat_id]
        if now - ts < _TTL_SECONDS:
            return ids
    admins = await bot.get_chat_administrators(chat_id)
    ids = [adm.user.id for adm in admins]
    _cache[chat_id] = (now, ids)
    return ids

