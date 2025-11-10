from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram import Bot

from utils.admins import get_admin_ids


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message, bot: Bot) -> bool:
        admin_ids = await get_admin_ids(bot, message.chat.id)
        return message.from_user.id in admin_ids

