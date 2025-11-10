from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.types import Message

from filters import AntiMat, AntiBegger

text_moderation_router = Router()

@text_moderation_router.message()
async def debug_all(message: Message):
    print(f"📩 ROUTER {__name__} отримав: {message.text}")


@text_moderation_router.message(AntiMat())
async def catch_mat(message: Message):
    mat_warn_text = (
        f"🚫 <b>{message.from_user.full_name}</b>, "
        "ваше повідомлення містило ненормативну лексику і було видалено."
    )
    await message.reply(mat_warn_text, parse_mode=ParseMode.HTML)
    await message.delete()

@text_moderation_router.message(AntiBegger())
async def block_begging(message: Message):
    begger_warn_text= (
         f"🚫 <b>{message.from_user.full_name}</b>, жебрацтво Заборонено! "
    )
    
    await message.reply(begger_warn_text, parse_mode=ParseMode.HTML)
    await message.delete()