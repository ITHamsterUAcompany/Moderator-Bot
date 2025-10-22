import asyncio
import os
from base64 import b64decode

from aiogram import Router
from aiogram.types import Message, BufferedInputFile, InputMediaPhoto
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode, ChatAction
from google.genai.errors import ServerError

import google.generativeai as genai
from utils.gemini import client as gpt_client
from handlers.wallet import get_balance, deduct_balance, add_balance
from config import GENIMGAI_API_KEY

ai_ask_router = Router()

COST_PER_PROMPT = 18  # ТК для тексту
COST_PER_IMAGE = 23   # ТК для картинки

# -------------------- GPT-текст --------------------
@ai_ask_router.message(Command(commands=["gpt"]))
async def ai_message_handler(message: Message, command: CommandObject) -> None:
    user_id = message.from_user.id
    balance = get_balance(user_id)

    if balance < COST_PER_PROMPT:
        await message.reply(f"❌ Недостатньо ТК. Баланс: {balance}")
        return

    client_prompt = command.args
    if not client_prompt:
        await message.reply("❌ Ви не вказали запит після /gpt")
        return

    if not deduct_balance(user_id, COST_PER_PROMPT):
        await message.reply("❌ Не вдалося списати ТК. Спробуйте ще раз.")
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    sent_message = await message.reply("⏳")

    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: gpt_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=client_prompt
            )
        )
    except ServerError:
        add_balance(user_id, COST_PER_PROMPT)
        await sent_message.delete()
        await message.reply("❌ Gemini перевантажена. ТК повернено.")
        return
    except Exception as e:
        add_balance(user_id, COST_PER_PROMPT)
        await sent_message.delete()
        await message.reply(f"❌ Помилка: {e}\nТК повернено.")
        return

    await sent_message.delete()
    try:
        await message.reply(response.text, parse_mode=ParseMode.HTML)
    except:
        await message.reply(f"❌ Не вдалося надіслати відповідь. Знято {COST_PER_PROMPT} ТК.")

    new_balance = get_balance(user_id)
    await message.reply(f"💸 Знято {COST_PER_PROMPT} ТК. Залишок: {new_balance}")


genai.configure(api_key=GENIMGAI_API_KEY)
# -------------------- GPT-картинка --------------------
@ai_ask_router.message(Command(commands=["gptimg"]))
async def ai_image_handler(message: Message, command: CommandObject):
    user_id = message.from_user.id
    balance = get_balance(user_id)

    if balance < COST_PER_IMAGE:
        await message.reply(f"❌ Недостатньо ТК. Баланс: {balance}")
        return

    prompt = command.args
    if not prompt:
        await message.reply("❌ Ви не вказали запит після /gptimg")
        return

    if not deduct_balance(user_id, COST_PER_IMAGE):
        await message.reply("❌ Не вдалося списати ТК.")
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO)
    wait_msg = await message.reply("🎨 Генерую зображення...")

    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: gpt_client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt]  # тільки 1 картинка
            )
        )

        # Беремо першу картинку
        candidate = response.candidates[0]
        part = candidate.content[0]
        b64 = part.get("image_base64") or part.get("inline_data", {}).get("data")
        if not b64:
            add_balance(user_id, COST_PER_IMAGE)
            await wait_msg.delete()
            await message.reply("❌ Модель не повернула зображення. ТК повернено.")
            return

        img_bytes = b64decode(b64)
        await wait_msg.delete()
        await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=BufferedInputFile(img_bytes, filename="result.jpg"),
            caption=f"{message.from_user.full_name} створив зображення"
        )

    except Exception as e:
        add_balance(user_id, COST_PER_IMAGE)
        await wait_msg.delete()
        await message.reply(f"❌ Помилка генерації: {e}\nТК повернено.")
        return

    new_balance = get_balance(user_id)
    await message.reply(f"✅ Зображення готове.\n💸 Знято {COST_PER_IMAGE} ТК. Баланс: {new_balance}")