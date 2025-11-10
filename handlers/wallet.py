import os
import json
import time
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message
from handlers.role_router import get_role

wallet_router = Router()

@wallet_router.message()
async def debug_all(message: Message):
    print(f"📩 ROUTER {__name__} отримав: {message.text}")

# 📁 Шлях до файлу з балансами
WALLET_FILE = os.path.join(os.path.dirname(__file__), "wallets.json")
START_TOKENS = 100
COOLDOWN_SECONDS = 50400  # 14 годин


# 💰 Структура: {user_id: {"balance": int, "last_claim": str, "last_topup": float}}
balances = {}

# 📦 Завантаження з файлу
if os.path.exists(WALLET_FILE):
    try:
        with open(WALLET_FILE, "r", encoding="utf-8") as f:
            balances = json.load(f)
    except Exception:
        balances = {}
else:
    with open(WALLET_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# 🧩 Збереження у файл
def save_wallets():
    os.makedirs(os.path.dirname(WALLET_FILE), exist_ok=True)
    with open(WALLET_FILE, "w", encoding="utf-8") as f:
        json.dump(balances, f, ensure_ascii=False, indent=2)

# 🪙 Отримати баланс
def get_balance(user_id: int) -> int:
    user_id = str(user_id)
    if user_id not in balances:
        balances[user_id] = {
            "balance": START_TOKENS,
            "last_claim": "1970-01-01 00:00:00",
            "last_topup": 0
        }
        save_wallets()
    return balances[user_id]["balance"]

# ➖ Списати ТК
def deduct_balance(user_id: int, amount: int) -> bool:
    user_id = str(user_id)
    get_balance(user_id)
    if balances[user_id]["balance"] >= amount:
        balances[user_id]["balance"] -= amount
        save_wallets()
        return True
    return False

# ➕ Додати ТК без обмежень
def add_balance(user_id: int, amount: int) -> None:
    user_id = str(user_id)
    get_balance(user_id)
    balances[user_id]["balance"] += amount
    save_wallets()

# 🔁 Встановити баланс напряму (для vip_router)
def set_balance(user_id: int, amount: int) -> None:
    user_id = str(user_id)
    get_balance(user_id)
    balances[user_id]["balance"] = amount
    save_wallets()

# ⏰ Перевірка cooldown
def can_claim(user_id: int) -> bool:
    user_id = str(user_id)
    last = datetime.strptime(balances.get(user_id, {}).get("last_claim", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")
    return datetime.now() - last >= timedelta(seconds=COOLDOWN_SECONDS)

# 💰 Видача бонусу
def claim_tokens(user_id: int, amount: int) -> bool:
    user_id = str(user_id)
    if not can_claim(user_id):
        return False
    get_balance(user_id)
    balances[user_id]["balance"] += amount
    balances[user_id]["last_claim"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_wallets()
    return True



# 👑 Перевірка адміна
async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        admins = await bot.get_chat_administrators(chat_id)
        return any(a.user.id == user_id for a in admins)
    except Exception:
        return False


# 💸 Поповнення балансу
@wallet_router.message(F.text.regexp(r"^\+[тt][кk]\s*\d+", flags=0))
async def add_tokens(message: Message, bot: Bot):
    now = time.time()
    user_id = str(message.from_user.id)
    target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    target_id = str(target_user.id)

    # Динамічна роль
    role = get_role(message.from_user.id) or "Адміністратор"

    # ✳️ Розділення на частини: +тк <сума>, <причина>
    parts = message.text.split(",", 1)
    first_part = parts[0].strip()
    reason = parts[1].strip() if len(parts) > 1 else None

    try:
        amount = int(first_part.split()[1])
    except (IndexError, ValueError):
        await message.reply("❌ Формат: <code>+тк 100, причина</code>")
        return

    get_balance(target_id)
    get_balance(user_id)

    admin_status = await is_admin(bot, message.chat.id, message.from_user.id)

    if not admin_status:
        elapsed = now - balances[user_id]["last_topup"]
        if elapsed < COOLDOWN_SECONDS:
            h, m = int((COOLDOWN_SECONDS - elapsed) // 3600), int(((COOLDOWN_SECONDS - elapsed) % 3600) // 60)
            await message.reply(f"⏳ Ти вже поповнював недавно. Повтори через {h} год {m} хв.")
            return

    balances[target_id]["balance"] += amount
    balances[user_id]["last_topup"] = now
    save_wallets()

    
    admin_role = get_role(message.from_user.id)


    if target_id == user_id:
        msg = f"💰 Баланс поповнено на <b>{amount}</b> ТК!\n🔹 Новий баланс: <b>{balances[target_id]['balance']}</b>"

    else:
        msg = (
            f"👑 {admin_role} <b>{message.from_user.full_name}</b> поповнив баланс користувачу "
            f"<b>{target_user.full_name}</b> на <b>{amount}</b> ТК!\n"
            f"💼 Новий баланс: <b>{balances[target_id]['balance']}</b>"
        )

    # ➕ Додаємо причину, якщо вона є
    if reason:
        msg += f"\n📝 Причина: <i>{reason}</i>"

    await message.reply(msg, parse_mode="HTML")


# 💼 Перевірка балансу
@wallet_router.message(F.text.lower().in_(["баланс", "гаманець", "кошелек"]))
async def check_balance(message: Message):
    balance = get_balance(message.from_user.id)
    await message.reply(f"💼 Твій поточний баланс: <b>{balance}</b> ТК", parse_mode="HTML")
