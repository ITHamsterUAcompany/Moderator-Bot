import asyncio
from datetime import datetime, timedelta
from typing import Optional

from aiogram import F, Router, Bot
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ChatPermissions, Message
from aiogram.filters.command import CommandObject

from ..filters import IsAdmin
from ..data_store import DataStore, HistoryEntry
from ..utils.parse import parse_duration_to_seconds


moderation_router = Router()
store = DataStore()


# text moderation handlers moved to text_moderation_router


@moderation_router.message(Command("replyreport"), IsAdmin())
async def reply_report(message: Message):
    admin_fullname = message.from_user.full_name
    admin_name = message.from_user.first_name
    role = "Адміністратор"
    phrases = [
        f"💬 <b>Відповідь від: {role} {admin_fullname} </b>\n\nВітаю, {admin_name} Мчить вам на допомогу.",
        f"💬 <b>Відповідь від: {role} {admin_fullname} </b> {admin_name} вже в дорозі!",
        f"💬 <b>Відповідь від: {role} {admin_fullname} </b>\n\n{admin_name} поспішає вам на допомогу!",
    ]
    import random

    first_text = random.choice(phrases)
    await message.answer(first_text, parse_mode="HTML")
    await asyncio.sleep(random.randint(3, 7))
    second_text = (
        f"💬 <b>Відповідь від {admin_fullname}</b>\n\n"
        f"Вітаю, мене звати {admin_name}, працюю по вашій Заявці."
    )
    await message.answer(second_text, parse_mode="HTML")


@moderation_router.message(Command("spec", "spectator"), IsAdmin())
async def spec_user(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return
    target_user = message.reply_to_message.from_user
    user_id = str(target_user.id)
    user_name = target_user.full_name
    chat_member = await bot.get_chat_member(chat_id=message.chat.id, user_id=target_user.id)
    status = chat_member.status
    role = "Адміністратор" if status in ["creator", "administrator"] else "Учасник"
    info_text = (
        f"<b>👤 Інформація про користувача:</b>\n"
        f"📝 Ім'я: {user_name}\n"
        f"🏷 Статус/Роль: {role}\n"
        f"🆔 ID: {user_id}\n"
    )
    if role == "Учасник":
        punishments = store.get_history(target_user.id)
        if punishments:
            info_text += "\n<b>👮 Історія покарань:</b>\n"
            for idx, p in enumerate(punishments, start=1):
                info_text += (
                    f"{idx}. ⛔ <b>Тип:</b> {p.get('type','')}\n"
                    f"   📌 <b>Причина:</b> {p.get('reason','')}\n"
                    f"   ⏰ <b>Дата:</b> {p.get('date','')}\n"
                    f"   📅 <b>До:</b> {p.get('until','—')}\n\n"
                )
        else:
            info_text += "\n✅ Покарань немає."
    await message.reply(info_text)


@moderation_router.message(Command("unban"))
async def unban_user(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return
    target_user = message.reply_to_message.from_user
    admin_fullname = message.from_user.full_name
    role = "Адміністратор"
    try:
        await bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            only_if_banned=True,
        )
        await message.answer(f"✅ {role} {admin_fullname} Розблокував користувача {target_user.full_name}")
    except Exception as e:
        await message.answer(f"❌ Помилка при розбані: {e}")


@moderation_router.message(Command("ban"))
async def ban_user(message: Message, command: CommandObject, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Використай: /ban <час або перманентний>, причина (у відповідь на повідомлення)")
        return
    args = command.args
    if not args:
        await message.reply("❗ Формат: /ban <час або перманентний>, причина")
        return
    parts = args.split(",", 1)
    duration_reason = parts[0].strip()
    reason = parts[1].strip() if len(parts) > 1 else "Не вказано"
    target_user = message.reply_to_message.from_user
    seconds, duration_text = parse_duration_to_seconds(duration_reason)
    try:
        until_date = None if seconds is None else datetime.now() + timedelta(seconds=seconds)
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            ),
            until_date=until_date,
        )
        await message.answer(
            f"⛔ Адміністратор {message.from_user.full_name} заблокував {target_user.full_name} "
            f"{duration_text if duration_text else 'назавжди'}.\n📋 Причина: {reason}"
        )
        store.append_history(
            target_user.id,
            HistoryEntry(
                type="ban",
                reason=reason,
                date=datetime.now().strftime("%d.%m.%Y %H:%M"),
                until=until_date.strftime("%d.%m.%Y %H:%M") if until_date else "Назавжди",
            ),
        )
    except Exception as e:
        await message.reply(f"❌ Помилка при бані: {e}")


@moderation_router.message(Command("mute"))
async def mute_user(message: Message, command: CommandObject, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Використай: /mute <час>, причина (у відповідь на повідомлення)")
        return
    args = command.args
    if not args:
        await message.reply("❗ Формат: /mute <час>, причина")
        return
    parts = args.split(",", 1)
    duration_reason = parts[0].strip()
    reason = parts[1].strip() if len(parts) > 1 else "Не вказано"
    target_user = message.reply_to_message.from_user
    seconds, duration_text = parse_duration_to_seconds(duration_reason)
    if not seconds:
        await message.reply("❗ Невірний формат часу. Використай: 10m, 2h, 7d")
        return
    until_date = datetime.now() + timedelta(seconds=seconds)
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date,
        )
        await message.answer(
            f"🔇 Адміністратор {message.from_user.full_name} видав мут "
            f"{target_user.full_name} на {duration_text}.\n📋 Причина: {reason}"
        )
        store.append_history(
            target_user.id,
            HistoryEntry(
                type="mute",
                reason=reason,
                date=datetime.now().strftime("%d.%m.%Y %H:%M"),
                until=until_date.strftime("%d.%m.%Y %H:%M"),
            ),
        )
        # No local mute tracking; rely on Telegram until_date
    except Exception as e:
        await message.reply(f"❌ Помилка при муті: {e}")


@moderation_router.message(Command("unmute"))
async def unmute_user(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return
    target_user = message.reply_to_message.from_user
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await message.answer(f"🔊 Адміністратор {message.from_user.full_name} зняв мут {target_user.full_name}.")
        # No local mute tracking to clear
    except Exception as e:
        await message.answer(f"❌ Помилка при знятті мута: {e}")


@moderation_router.message(Command("kick"))
async def kick_user(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return
    target_user = message.reply_to_message.from_user
    reason = "Без причини"
    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            until_date=datetime.now() + timedelta(seconds=30),
        )
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user.id)
        store.append_history(
            target_user.id,
            HistoryEntry(
                type="kick",
                reason=reason,
                date=datetime.now().strftime("%d.%m.%Y %H:%M"),
                until="—",
            ),
        )
        await message.answer(
            f"👢 Адміністратор {message.from_user.full_name} від’єднав {target_user.full_name}.\n📌 Причина: {reason}"
        )
    except Exception as e:
        await message.reply(f"❌ Помилка при виконанні кіку: {e}")


@moderation_router.message(Command("warn"), IsAdmin())
async def warn_user(message: Message, command: CommandObject):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return
    target_user = message.reply_to_message.from_user
    reason = command.args if command.args else "Без причини"
    store.append_history(
        target_user.id,
        HistoryEntry(
            type="warn",
            reason=reason,
            date=datetime.now().strftime("%d.%m.%Y %H:%M"),
            until="—",
        ),
    )
    await message.answer(
        f"⚠️ Адміністратор {message.from_user.full_name} попередив {target_user.full_name}.\n📝 Причина: {reason}"
    )


@moderation_router.message(Command("unwarn"), IsAdmin())
async def unwarn_user(message: Message):
    args = message.text.split()
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(args) >= 2:
        # Attempt to resolve only within reply context kept simple
        await message.reply("<b>❗ Використайте reply для зняття попередження.</b>")
        return
    else:
        await message.reply("<b>❗ Формат: /unwarn (у відповідь на повідомлення)</b>")
        return
    removed = store.pop_last_warn(target_user.id)
    if removed:
        await message.answer(
            f"✅ Адміністратор {message.from_user.full_name} зняв попередження у {target_user.full_name}.\n"
        )
    else:
        await message.reply(f"<b>❗ У користувача {target_user.full_name} немає попереджень для зняття.</b>")

