import os
import json

ROLES_FILE = os.path.join(os.path.dirname(__file__), "role.json")

# --- Ієрархія посад ---
ROLE_LEVELS = {
    "ГА": 100,
    "ЗГА": 90,
    "Куратор": 80,
    "Старший Адміністратор": 70,
    "А - 8": 60,
    "А - 7": 55,
    "А - 6": 50,
    "А - 5": 45,
    "А - 4": 40,
    "А - 3": 35,
    "А - 2": 30,
    "Тех помічник": 20,
}

# --- Завантаження ролей ---
if os.path.exists(ROLES_FILE):
    with open(ROLES_FILE, "r", encoding="utf-8") as f:
        roles = json.load(f)
else:
    roles = {r: [] for r in ROLE_LEVELS.keys()}
    with open(ROLES_FILE, "w", encoding="utf-8") as f:
        json.dump(roles, f, ensure_ascii=False, indent=2)


def save_roles():
    with open(ROLES_FILE, "w", encoding="utf-8") as f:
        json.dump(roles, f, ensure_ascii=False, indent=2)


# --- Основні методи ---
def get_role(user_id: int) -> str:
    """Повертає роль користувача або 'Користувач'"""
    user_id = int(user_id)
    for role, ids in roles.items():
        if user_id in ids:
            return role
    return "Користувач"


def set_role(user_id: int, role: str):
    """Встановлює роль користувачу"""
    user_id = int(user_id)
    if role not in ROLE_LEVELS:
        raise ValueError("❌ Невідома роль!")

    # Видаляємо користувача з усіх інших ролей
    for r in roles.values():
        if user_id in r:
            r.remove(user_id)

    # Додаємо до потрібної
    roles[role].append(user_id)
    save_roles()


def remove_role(user_id: int):
    """Видаляє користувача з усіх ролей"""
    user_id = int(user_id)
    changed = False
    for ids in roles.values():
        if user_id in ids:
            ids.remove(user_id)
            changed = True
    if changed:
        save_roles()


def get_role_level(user_id: int) -> int:
    """Повертає рівень ролі користувача"""
    role = get_role(user_id)
    return ROLE_LEVELS.get(role, 0)


def has_permission(user_id: int, min_role: str) -> bool:
    """Перевірка — чи має користувач достатній рівень для дії"""
    return get_role_level(user_id) >= ROLE_LEVELS.get(min_role, 0)
