from aiogram import Router
from aiogram.types import Message

offtop_router = Router()

@offtop_router.message()
async def debug_all(message: Message):
    print(f"📩 ROUTER {__name__} отримав: {message.text}")


@offtop_router.message(lambda m: m.text and m.text.lower().startswith("!оффтоп"))
async def user_offtop(message: Message):
    """Дозволяє користувачам публікувати оффтоп (не по темі)."""
    text = message.text[len("!оффтоп"):].strip()

    if not text:
        await message.reply(
            "💬 Напиши текст після команди!\n"
            "Приклад: `!оффтоп як вам новий апдейт?`"
        )
        return
    await message.delete()
    user = message.from_user
    formatted = (
        f"🗨️ <b>Оффтоп від {user.full_name}:</b>\n{text}"
    )

    # Відправляємо красиво оформлене повідомлення
    await message.answer(formatted, parse_mode="HTML")
5