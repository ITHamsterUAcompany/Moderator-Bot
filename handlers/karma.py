from datetime import datetime, timedelta
from aiogram import F, Router, Bot
from aiogram.types import Message
from re import Match
from data_store import DataStore

from filters import IsAdmin

karma_router = Router()

VOTE_COOLDOWN = 12 * 60 * 60  # 12 годин у секундах
@karma_router.message()
async def debug_all(message: Message):
    print(f"📩 ROUTER {__name__} отримав: {message.text}")


# ------------------ СКИДАННЯ КАРМИ ------------------
@karma_router.message(F.text.startswith("resetkarma"), IsAdmin())
async def reset_karma(message: Message, store: DataStore, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача, якому потрібно скинути карму.")
        return

    target_user = message.reply_to_message.from_user

    try:
        store.set_karma(user_id=target_user.id, value=0)
        await message.reply(
            f"♻️ Адміністратор <b>{message.from_user.full_name}</b> скинув карму користувачу <b>{target_user.full_name}</b> до <b>0</b>."
        )
    except Exception as e:
        await message.reply(f"❌ Помилка при скиданні карми: {type(e).__name__}: {e}")


# ------------------ ПІДВИЩЕННЯ КАРМИ ------------------
@karma_router.message(F.reply_to_message, F.text.regexp(r"^\+?\d+$").as_("digits"))
async def handle_karma_plus(message: Message, digits: Match[str], store: DataStore):
    voter_id = str(message.from_user.id)
    target_user = message.reply_to_message.from_user
    now = datetime.now().timestamp()

    store.data.setdefault("last_votes", {})
    last_vote_time = store.data["last_votes"].get(voter_id)
    if last_vote_time and now - last_vote_time < VOTE_COOLDOWN:
        remaining = int((VOTE_COOLDOWN - (now - last_vote_time)) / 3600)
        await message.reply(f"⏳ Ти вже голосував(ла)! Можна буде знову через {remaining} годин.")
        return

    value = int(digits.group(0).replace("+", ""))
    new_karma = store.add_karma(target_user.id, value)

    store.data["last_votes"][voter_id] = now
    store.save()

    await message.reply(
        f"💫 <b>{message.from_user.full_name}</b> підвищив(ла) карму користувачу <b>{target_user.full_name}</b> на <code>{value}</code>.\n"
        f"⚖️ Поточна карма: <b>{new_karma}</b>\n"
        f"(Макс: 1000 | Мін: -1000)"
    )


# ------------------ ЗНИЖЕННЯ КАРМИ ------------------
@karma_router.message(F.reply_to_message, F.text.regexp(r"^-\d+$").as_("digits"))
async def handle_karma_minus(message: Message, digits: Match[str], store: DataStore):
    voter_id = str(message.from_user.id)
    target_user = message.reply_to_message.from_user
    now = datetime.now().timestamp()

    store.data.setdefault("last_votes", {})
    last_vote_time = store.data["last_votes"].get(voter_id)
    if last_vote_time and now - last_vote_time < VOTE_COOLDOWN:
        remaining = int((VOTE_COOLDOWN - (now - last_vote_time)) / 3600)
        await message.reply(f"⏳ Ти вже голосував(ла)! Можна буде знову через {remaining} годин.")
        return

    value = int(digits.group(0))
    new_karma = store.add_karma(target_user.id, value)

    store.data["last_votes"][voter_id] = now
    store.save()

    await message.reply(
        f"💢 <b>{message.from_user.full_name}</b> знизив(ла) карму користувачу <b>{target_user.full_name}</b> на <code>{abs(value)}</code>.\n"
        f"⚖️ Поточна карма: <b>{new_karma}</b>\n"
        f"(Макс: 1000 | Мін: -1000)"
    )