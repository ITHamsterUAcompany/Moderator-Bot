import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from utils.gemini import client
from google.genai.errors import ServerError

from handlers.wallet import get_balance, deduct_balance

ai_ask_router = Router()

COST_PER_PROMPT = 18  # вартість 1 запиту GPT

@ai_ask_router.message(Command(commands=["gpt"]))
async def ai_message_handler(message: Message, command: CommandObject) -> None:
    user_id = message.from_user.id
    balance = get_balance(user_id)

    if balance < COST_PER_PROMPT:
        await message.reply(f"❌ Недостатньо ТК. Баланс: {balance}")
        return

    client_prompt = command.args
    if not client_prompt:
        await message.reply("❌ Ви не вказали запит для GPT.")
        return

    sent_message = await message.reply("⏳")

    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-2.5-flash",
                contents=client_prompt
            )
        )
    except ServerError:
        await sent_message.delete()
        await message.reply("❌ Gemini перевантажена, спробуйте пізніше.")
        return
    except Exception as e:
        await sent_message.delete()
        await message.reply(f"❌ Виникла помилка: {e}")
        return

    await sent_message.delete()
    await message.reply(response.text, parse_mode="HTML")

    # списуємо ТК
    deduct_balance(user_id, COST_PER_PROMPT)
    updated_balance = get_balance(user_id)
    await message.reply(f"💸 Знято {COST_PER_PROMPT} ТК. Залишок: {updated_balance}")