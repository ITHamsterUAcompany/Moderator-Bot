
from aiogram import Router, types, Bot
from datetime import datetime, timedelta
from aiogram.types import Message
from config import settings
from data_store import store
from handlers.wallet import get_balance, set_balance
vip_router = Router()

@vip_router.message()
async def debug_all(message: Message):
    print(f"📩 ROUTER {__name__} отримав: {message.text}")

# 💰 Ціни VIP у токенах (ТК)
VIP_PRICES = {
    60: 35,
    30: 26,
    14: 15,
    7: 10,
    3: 5
}


# ------------------- VIP логіка -------------------
def cleanup_expired_vips():
    """Видаляє всіх у кого закінчився VIP."""
    store.refresh()
    vip_data = store.data.get("vip_users", {})
    if not vip_data:
        return

    now = datetime.now()
    removed = []
    for uid, expiry in list(vip_data.items()):
        try:
            if datetime.fromisoformat(expiry) < now:
                del vip_data[uid]
                removed.append(uid)
        except Exception:
            del vip_data[uid]

    if removed:
        store.save()
        print(f"[VIP CLEANUP] Видалено {len(removed)} користувачів: {', '.join(removed)}")


def add_vip(user_id: int, days: int):
    """Додає або продовжує VIP-підписку користувача."""
    cleanup_expired_vips()
    store.refresh()
    uid = str(user_id)
    now = datetime.now()

    vip_data = store.data.setdefault("vip_users", {})

    # Якщо користувач уже має активний VIP — додаємо дні до поточної дати закінчення
    if uid in vip_data:
        try:
            expires = datetime.fromisoformat(vip_data[uid])
            if expires > now:
                expires_at = expires + timedelta(days=days)
            else:
                expires_at = now + timedelta(days=days)
        except Exception:
            expires_at = now + timedelta(days=days)
    else:
        expires_at = now + timedelta(days=days)

    vip_data[uid] = expires_at.isoformat()
    store.save()
    return expires_at


def has_active_vip(user_id: int) -> bool:
    """Перевіряє чи діє VIP."""
    cleanup_expired_vips()
    store.refresh()
    uid = str(user_id)
    vip_data = store.data.get("vip_users", {})
    if uid not in vip_data:
        return False
    try:
        expires = datetime.fromisoformat(vip_data[uid])
        return datetime.now() < expires
    except Exception:
        return False


def is_admin_or_vip(user_id: int, chat_member_status: str) -> bool:
    """Перевіряє чи користувач адмін або має VIP."""
    if chat_member_status in ["creator", "administrator"]:
        return True
    return has_active_vip(user_id)


# ------------------- Купівля VIP -------------------
@vip_router.message(lambda m: m.text and (m.text.lower().startswith("!buyvip") or m.text.lower().startswith("/buyvip")))
async def buy_vip_command(message: types.Message):
    cleanup_expired_vips()

    text = message.text.strip().replace(",", " ").split()
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    if len(text) != 2 or not text[1].isdigit():
        prices = "\n".join([f"• {d} днів — {p} ТК" for d, p in VIP_PRICES.items()])
        await message.reply(
            "💎 <b>Купівля VIP</b>\n"
            "Формат: <code>!buyvip, 30</code>\n\n"
            "Доступні варіанти:\n" + prices
        )
        return

    days = int(text[1])
    if days not in VIP_PRICES:
        await message.reply("❌ Недійсний термін. Доступні: 3, 7, 14, 30, 60 днів.")
        return

    price = VIP_PRICES[days]
    balance = get_balance(user_id)

    if balance < price:
        await message.reply(f"🚫 Недостатньо коштів! Потрібно {price} ТК, у тебе {balance} ТК.")
        return

    set_balance(user_id, balance - price)
    expires_at = add_vip(user_id, days)

    await message.reply(
        f"✅ <b>{user_name}</b>, ти придбав <b>VIP</b> на <b>{days} днів</b>\n"
        f"💰 Знято <b>{price} ТК</b>\n"
        f"⏳ Діє до: <code>{expires_at.strftime('%d.%m.%Y %H:%M')}</code>"
    )


# ------------------- VIP повідомлення -------------------
@vip_router.message(lambda m: m.text and (m.text.lower().startswith("!vip") or m.text.lower().startswith("/vip")))
async def vip_chat_command(message: types.Message, bot: Bot):
    cleanup_expired_vips()

    user_id = message.from_user.id
    user_name = message.from_user.full_name
    chat_member = await bot.get_chat_member(message.chat.id, user_id)
    text = message.text.strip().split(maxsplit=1)

    if len(text) == 1:
        await message.reply("📣 Використай: <code>!vip твій_текст</code>")
        return

    if not is_admin_or_vip(user_id, chat_member.status):
        await message.reply("🚫 Лише для користувачів із активним <b>VIP</b> або адміністраторів.")
        return

    vip_message = text[1]
    await message.answer(f"💬 <b>[VIP]</b> {user_name}: {vip_message}")