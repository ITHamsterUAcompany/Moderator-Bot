import asyncio
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode, ChatAction

from utils.gemini import client
from google.genai.errors import ServerError

# гаманець
from handlers.wallet import get_balance, deduct_balance, add_balance

ai_ask_router = Router()

COST_PER_PROMPT = 18  # 💸 вартість GPT-запиту


@ai_ask_router.message(Command(commands=["gpt"]))
async def ai_message_handler(message: Message, command: CommandObject) -> None:
    user_id = message.from_user.id
    balance = get_balance(user_id)

    # 1) Перевірка балансу
    if balance < COST_PER_PROMPT:
        await message.reply(f"❌ Недостатньо ТК. Баланс: {balance}")
        return

    client_prompt = command.args
    if not client_prompt:
        await message.reply("❌ Ви не вказали запит після /gpt")
        return

    # 2) Списання ТК ПЕРЕД викликом API
    if not deduct_balance(user_id, COST_PER_PROMPT):
        await message.reply("❌ Не вдалося списати ТК. Спробуйте ще раз.")
        return

    # показуємо action typing
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING
    )

    sent_message = await message.reply("⏳")

    # 3) Виклик Gemini
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
        # повертаємо ТК якщо Gemini впала
        add_balance(user_id, COST_PER_PROMPT)
        await sent_message.delete()
        await message.reply("❌ Gemini перевантажена. ТК повернено.")
        return

    except Exception as e:
        # повертаємо ТК при інших помилках
        add_balance(user_id, COST_PER_PROMPT)
        await sent_message.delete()
        await message.reply(f"❌ Помилка: {e}\nТК повернено.")
        return

    # 4) Успішно — прибираємо “⏳”, шлемо відповідь
    await sent_message.delete()

    try:
        await message.reply(response.text, parse_mode=ParseMode.HTML)
    except:
        await message.reply(f"❌ Не вдалося надіслати відповідь. Знято {COST_PER_PROMPT} ТК.")

    # 5) Фінал — показуємо новий баланс
    new_balance = get_balance(user_id)
    await message.reply(f"💸 Знято {COST_PER_PROMPT} ТК. Залишок: {new_balance}")
