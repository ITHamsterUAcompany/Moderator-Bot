import os
import asyncio
from datetime import datetime
from aiogram import F, Router, Bot
from aiogram.types import (
    Message,
    ChatPermissions,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from filters import IsAdmin
from data_store import DataStore, HistoryEntry, store
from utils.parse import parse_duration_to_seconds
from handlers.wallet import get_balance
from handlers.role_router import get_role  # ✅ Динамічна роль

# === Основний router ===
moderation_router = Router()

SENIOR_ADMINS = [1071891595]


# ✅ Debug — тепер не блокує команди
@moderation_router.message(F.text & ~F.text.startswith("/"))
async def debug_all(message: Message):
    print(f"📩 ROUTER {__name__} отримав: {message.text}")


# ------------------ VANINVITE ------------------
@moderation_router.message(Command("vaninvite"))
async def remove_admin_self(message: Message, bot: Bot):
    chat_id = message.chat.id
    user = message.from_user

    try:
        # 1️⃣ Знімаємо права адміністратора (через restrict)
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
            ),
        )

        # 2️⃣ Повідомлення у групу
        await message.reply(
            f"✅ <b>{user.full_name}</b> Звільнений.\n"
            f"📄 Причина: <i>ЗВБ — за власним бажанням</i>",
            parse_mode="HTML",
        )

    except TelegramForbiddenError:
        await message.reply("❌ Бот не має прав змінювати статуси учасників.")
    except TelegramBadRequest:
        await message.reply(
            "⚠️ Неможливо понизити цього адміністратора (можливо, він власник групи)."
        )
    except Exception as e:
        await message.reply(f"⚠️ Виникла помилка: {e}")


# ------------------ ADMIN ANNOUNCE ------------------
@moderation_router.message(Command("adminannounce"))
async def announce_admin_recruitment(message: Message):
    if message.from_user.id not in SENIOR_ADMINS:
        await message.reply("⛔ Ця команда доступна лише старшому складу адміністрації.")
        return

    image_path = "handlers/banner.jpg"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Подати анкету",
                    url="https://forms.gle/gC8uz7ASZSfrhxhw7",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Статус заявки",
                    url="https://docs.google.com/spreadsheets/d/1i2hzZpSLVtqFSPq51fzcsMCbzFBMD0M52epekc47CSQ/edit?usp=sharing",
                )
            ],
        ]
    )

    text = (
        "<b>📣 Набір Адміністраторів у команду!</b>\n\n"
        "Хочеш стати частиною команди модераторів? 🛡️\n"
        "Ми шукаємо активних, уважних і доброзичливих людей, "
        "готових підтримувати порядок у спільноті.\n\n"
        "🔹 <b>Вимоги:</b>\n"
        "• Бути комунікабельним, грамотним, відповідальним, адекватним та стресостійким\n"
        "• Позитивний соціальний рейтинг\n"
        "• Середній добовий онлайн — від 3 годин\n"
        "• Вік — від 17 років (можливе виключення з 16)\n\n"
        "⚠️ <i>Примітка:</i> За обман Адміністрації — <b>блокування</b>\n\n"
        "👇 Обери дію нижче:"
    )

    try:
        if os.path.exists(image_path):
            await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=FSInputFile(image_path),
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        else:
            await message.bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
    except Exception as e:
        await message.reply(
            f"❌ Помилка при відправці оголошення:\n<code>{type(e).__name__}: {e}</code>",
            parse_mode="HTML",
        )


# ------------------ ЛОГ ПОКАРАНЬ ------------------
def log_punishment(
    message: Message, target_user, punishment_type, duration_text=None, reason="Не вказано"
):
    admin_name = message.from_user.full_name
    admin_id = message.from_user.id
    role = get_role(admin_id) or "Адміністратор"
    target_name = target_user.full_name

    if punishment_type == "ban":
        text = (
            f"⛔ <b>{role}</b> {admin_name} заблокував {target_name} "
            f"{duration_text if duration_text else 'назавжди'}.\n📋 Причина: {reason}"
        )
    elif punishment_type == "mute":
        text = f"🔇 <b>{role}</b> {admin_name} видав мут {target_name} на {duration_text}.\n📋 Причина: {reason}"
    elif punishment_type == "kick":
        text = f"👢 <b>{role}</b> {admin_name} від’єднав {target_name}.\n📌 Причина: {reason}"
    elif punishment_type == "warn":
        text = f"⚠️ <b>{role}</b> {admin_name} попередив {target_name}.\n📝 Причина: {reason}"
    else:
        text = f"❗ Невідомий тип покарання для {target_name}"

    store.append_history(
        target_user.id,
        HistoryEntry(
            type=punishment_type,
            reason=reason,
            date=datetime.now().strftime("%d.%m.%Y %H:%M"),
            text=text,
        ),
    )
    return text


# ------------------ REPLY REPORT ------------------
@moderation_router.message(Command("replyreport"), IsAdmin())
async def reply_report(message: Message):
    import random

    admin_id = message.from_user.id
    admin_fullname = message.from_user.full_name
    admin_name = message.from_user.first_name
    role = get_role(admin_id) or "Адміністратор"

    phrases = [
        f"💬 <b>Відповідь від: {role} {admin_fullname}</b>\n\nВітаю, {admin_name} мчить вам на допомогу.",
        f"💬 <b>Відповідь від: {role} {admin_fullname}</b> {admin_name} вже в дорозі!",
        f"💬 <b>Відповідь від: {role} {admin_fullname}</b>\n\n{admin_name} поспішає вам на допомогу!",
    ]
    await message.answer(random.choice(phrases), parse_mode="HTML")
    await asyncio.sleep(random.randint(3, 7))
    await message.answer(
        f"💬 <b>Відповідь від {admin_fullname}</b>\n\nВітаю, мене звати {admin_name}, працюю по вашій заявці.",
        parse_mode="HTML",
    )


# ------------------ UNBAN ------------------
@moderation_router.message(Command("unban"), IsAdmin())
async def unban_user(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return

    target_user = message.reply_to_message.from_user
    admin_fullname = message.from_user.full_name
    role = get_role(message.from_user.id) or "Адміністратор"

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
        await bot.unban_chat_member(
            chat_id=message.chat.id, user_id=target_user.id, only_if_banned=True
        )
        await message.answer(
            f"✅ <b>{role}</b> {admin_fullname} розблокував користувача <b>{target_user.full_name}</b>",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"❌ Помилка при розбані: {e}")
