from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.types import Message

from filters import AntiMat, AntiBegger


text_moderation_router = Router()


@text_moderation_router.message(AntiMat())
async def catch_mat(message: Message):
    await message.delete()
    warn_text = (
        f"🚫 <b>{message.from_user.full_name}</b>, "
        "ваше повідомлення містило ненормативну лексику і було видалено."
    )
    await message.answer(warn_text, parse_mode=ParseMode.HTML)


@text_moderation_router.message(AntiBegger())
async def block_begging(message: Message):
    await message.delete()

