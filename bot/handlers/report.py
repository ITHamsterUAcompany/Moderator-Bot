from datetime import datetime

import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..config import settings

# Simple in-memory cooldown state
last_report_time = {}


report_router = Router()


@report_router.message(Command("report"))
async def report_user(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("<b>❗ Вкажіть причину: /report <причина></b>")
        return
    reporter = message.from_user
    reporter_id = str(reporter.id)
    now = datetime.now()
    if reporter_id in last_report_time:
        time_diff = (now - last_report_time[reporter_id]).total_seconds()
        if time_diff < 180:
            await message.reply("<b>⏳ Ви зможете знову надіслати репорт через 3 хвилини.</b>")
            return
    last_report_time[reporter_id] = now
    reason = " ".join(args[1:])
    reported_user = message.reply_to_message.from_user if message.reply_to_message else None
    reporter_name = reporter.full_name
    if reported_user:
        reported_name = reported_user.full_name
        reported_id = reported_user.id
    else:
        reported_name = "❓ Невідомо (без reply)"
        reported_id = "—"
    now_str = now.strftime("%d.%m.%Y %H:%M:%S")
    report_msg = (
        f"🚨 **Новий репорт!**\n"
        f"👤 Від: {reporter_name} (`{reporter_id}`)\n"
        f"🎯 На: {reported_name} (`{reported_id}`)\n"
        f"🕒 Час: {now_str}\n"
        f"📌 Причина: {reason}"
    )
    async with aiohttp.ClientSession() as session:
        await session.post(settings.DISCORD_WEBHOOK_URL, json={"content": report_msg})
    await message.reply("<b>✅ Ви відправили репорт. Очікуйте на відповідь адміністратора.</b>")

