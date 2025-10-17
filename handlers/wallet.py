from aiogram import Router

import json
import os
from datetime import datetime, timedelta

# 📁 шлях до збереження балансів
WALLET_FILE = "wallets.json"

# 💰 пам’ять у форматі {user_id: {"balance": int, "last_claim": "YYYY-MM-DD HH:MM:SS"}}
balances = {}

wallet_router = Router()
# 📦 завантаження балансів із файлу
if os.path.exists(WALLET_FILE):
    try:
        with open(WALLET_FILE, "r", encoding="utf-8") as f:
            balances = json.load(f)
    except Exception:
        balances = {}

# 🧩 Збереження у файл
def save_wallets():
    os.makedirs(os.path.dirname(WALLET_FILE), exist_ok=True)
    with open(WALLET_FILE, "w", encoding="utf-8") as f:
        json.dump(balances, f, ensure_ascii=False, indent=2)

# 🪙 Отримати баланс користувача
def get_balance(user_id: int) -> int:
    user_id = str(user_id)
    if user_id not in balances:
        balances[user_id] = {"balance": 100, "last_claim": "1970-01-01 00:00:00"}  # стартові 100 ТК
        save_wallets()
    return balances[user_id]["balance"]

# ➕ Поповнити баланс
def add_balance(user_id: int, amount: int):
    user_id = str(user_id)
    get_balance(user_id)
    balances[user_id]["balance"] += amount
    save_wallets()

# ➖ Списати ТК
def deduct_balance(user_id: int, amount: int):
    user_id = str(user_id)
    get_balance(user_id)
    if balances[user_id]["balance"] >= amount:
        balances[user_id]["balance"] -= amount
        save_wallets()
        return True
    return False

# ⏰ Перевірка cooldown 14 годин
def can_claim(user_id: int) -> bool:
    user_id = str(user_id)
    last = datetime.strptime(balances.get(user_id, {}).get("last_claim", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")
    return datetime.now() - last >= timedelta(hours=14)

# 💰 Видача бонусу
def claim_tokens(user_id: int, amount: int):
    user_id = str(user_id)
    if not can_claim(user_id):
        return False
    balances[user_id]["balance"] += amount
    balances[user_id]["last_claim"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_wallets()
    return True