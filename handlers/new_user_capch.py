# captcha_router_with_storage.py
import asyncio
import json
from pathlib import Path
from typing import Dict, Set, Tuple

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, Message, CallbackQuery, ChatPermissions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

DATA_FILE = Path("Bot_data.json")

captcha_router = Router()

# --- завантаження даних
if DATA_FILE.exists():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        bot_data = json.load(f)
else:
    bot_data = {
        "muted_users": {},
        "warnings": {},
        "karma": {},
        "history": {},
        "banned_users": [],
        "last_votes": {},
        "capcha_user_status": {}
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(bot_data, f, ensure_ascii=False, indent=4)

# --- стан капчі
pending_first_message: Dict[int, Set[int]] = {}  # chat_id -> set(user_id)
pending_captcha: Dict[Tuple[int,int], int] = {}  # (chat_id,user_id) -> message_id
verified_users: Dict[int, Set[int]] = {}  # chat_id -> set(user_id)

# ---------- HELPERS ----------
def _add_pending_first(chat_id: int, user_id: int):
    pending_first_message.setdefault(chat_id,set()).add(user_id)

def _remove_pending_first(chat_id: int, user_id: int):
    s = pending_first_message.get(chat_id)
    if s:
        s.discard(user_id)
        if not s:
            pending_first_message.pop(chat_id,None)

def _mark_verified(chat_id: int, user_id: int):
    verified_users.setdefault(chat_id,set()).add(user_id)
    bot_data["capcha_user_status"][str(user_id)] = "successful"
    save_data()

def _is_verified(chat_id: int, user_id: int) -> bool:
    return user_id in verified_users.get(chat_id,set())

def _is_waiting_first(chat_id: int, user_id: int) -> bool:
    return user_id in pending_first_message.get(chat_id,set())

def _is_pending_captcha(chat_id: int, user_id: int) -> bool:
    return (chat_id,user_id) in pending_captcha

# ---------- 1) chat_member handler ----------
@captcha_router.chat_member()
async def on_chat_member_update(update: ChatMemberUpdated):
    new = update.new_chat_member
    if not new or getattr(new,"status",None) != "member":
        return
    chat_id = update.chat.id
    user_id = new.user.id
    if _is_verified(chat_id,user_id):
        return
    _add_pending_first(chat_id,user_id)

# ---------- 2) Перші повідомлення ----------
@captcha_router.message(F.chat.type.in_({"group","supergroup"}))
async def on_group_message(message: Message):
    if not message.from_user:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    if _is_verified(chat_id,user_id):
        return
    # якщо чекаємо першого повідомлення
    if _is_waiting_first(chat_id,user_id):
        try: await message.delete()
        except TelegramBadRequest: pass
        _remove_pending_first(chat_id,user_id)
        # кнопка капчі
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Я не бот", callback_data=f"captcha_ok:{chat_id}:{user_id}")
        kb.adjust(1)
        try:
            sent = await message.answer(
                f"{message.from_user.full_name}, підтвердіть, що ви не бот протягом 2 хвилин.",
                reply_markup=kb.as_markup()
            )
        except TelegramBadRequest:
            return
        pending_captcha[(chat_id,user_id)] = sent.message_id
        bot_data["capcha_user_status"][str(user_id)] = "pending"
        save_data()
        asyncio.create_task(_captcha_timer(chat_id,user_id,message.from_user.full_name))
        return
    # якщо капча вже показана — видаляємо повідомлення
    if _is_pending_captcha(chat_id,user_id):
        try: await message.delete()
        except TelegramBadRequest: pass
        return

# ---------- 3) Callback натиск кнопки ----------
@captcha_router.callback_query(F.data.startswith("captcha_ok:"))
async def on_captcha_click(callback: CallbackQuery):
    try:
        _,chat_id_s,user_id_s = callback.data.split(":")
        chat_id,user_id = int(chat_id_s),int(user_id_s)
    except:
        return await callback.answer("Неправильна капча",show_alert=True)
    if callback.from_user.id != user_id:
        return await callback.answer("Це не ваша капча",show_alert=True)
    if not _is_pending_captcha(chat_id,user_id):
        return await callback.answer("Капча вже не активна",show_alert=True)
    try:
        await callback.message.delete()
    except TelegramBadRequest: pass
    pending_captcha.pop((chat_id,user_id),None)
    _mark_verified(chat_id,user_id)
    await callback.answer("✅ Капчу пройдено")

# ---------- 4) Таймер 2 хв ----------
async def _captcha_timer(chat_id:int,user_id:int,full_name:str):
    await asyncio.sleep(120)
    if not _is_pending_captcha(chat_id,user_id):
        return
    pending_captcha.pop((chat_id,user_id),None)
    # бан користувача у Bot_data.json
    uid_str = str(user_id)
    bot_data["capcha_user_status"][uid_str] = "failed"
    if user_id not in bot_data["banned_users"]:
        bot_data["banned_users"].append(user_id)
    save_data()
    bot = captcha_router.bot
    try:
        await bot.send_message(chat_id,f"{full_name} не пройшов капчу та отримав Перманентне блокування")
    except TelegramBadRequest: pass

# ---------- 5) Запасна команда /capcha через реплай ----------
@captcha_router.message(Command("capcha"))
async def command_capcha(message:Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("Використай команду як реплай на користувача, якого потрібно перевірити.")
        return
    target = message.reply_to_message.from_user
    chat_id,user_id = message.chat.id,target.id
    if _is_verified(chat_id,user_id):
        await message.reply("Цей користувач вже пройшов капчу.")
        return
    if _is_pending_captcha(chat_id,user_id):
        await message.reply("Капча вже активна для цього користувача.")
        return
    _remove_pending_first(chat_id,user_id)
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Я не бот", callback_data=f"captcha_ok:{chat_id}:{user_id}")
    kb.adjust(1)
    try:
        sent = await message.reply(
            f"{target.full_name}, натисніть кнопку протягом 2 хвилин, щоб підтвердити, що ви не бот.",
            reply_markup=kb.as_markup()
        )
    except TelegramBadRequest:
        await message.reply("Не вдалося відправити капчу (можливо у бота немає прав).")
        return
    pending_captcha[(chat_id,user_id)] = sent.message_id
    bot_data["capcha_user_status"][str(user_id)] = "pending"
    save_data()
    asyncio.create_task(_captcha_timer(chat_id,user_id,target.full_name))
