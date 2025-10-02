import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command  , CommandObject
from utils.gemini import client
from google.genai.errors import ServerError

ai_ask_router  = Router()


@ai_ask_router.message(Command(commands=["ask-ai"]))
async def ai_message_handler(message: Message, command: CommandObject) -> None:
    stop_event = asyncio.Event()

    try:
        client_prompt = command.args

        sent_message = await message.reply("⏳")
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, lambda: client.models.generate_content(
            model="gemini-2.5-flash",
            contents=client_prompt
        ))

    except ServerError as e:
        stop_event.set()
        await message.reply("❌ гемені перегружена, спробуйте пізніше.")
        await sent_message.delete()

        return

    except Exception as e:
        stop_event.set()
        await message.reply(f"❌ Виникла помилка : {e}")
        await message.reply(str(e))
        await sent_message.delete()

        return

    stop_event.set()
    await sent_message.delete()

    await message.reply(response.text  , parse_mode="HTML")