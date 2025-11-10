from aiogram import Bot, Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message 

from data_store import DataStore 

# Припустимо, що у вас є імпортований Dispatcher, як ви вказали:
user_info_router = Router()
# --- ВИПРАВЛЕНИЙ ТРИГЕР: Ти хто / Хто ти ---

@user_info_router.message()
async def debug_all(message: Message):
    print(f"📩 ROUTER {__name__} отримав: {message.text}")

# Фільтр спрацьовує, якщо текст (у нижньому регістрі та без пробілів по краях) 
# дорівнює "ти хто" АБО "хто ти", І це є відповіддю.
@user_info_router.message(
    (F.text.lower().strip() == "ти хто") | (F.text.lower().strip() == "хто ти"),
    F.reply_to_message
)
async def who_are_you_trigger_reply(message: Message, bot: Bot, store: DataStore):
    """
    Обробник, який спрацьовує, якщо текст повідомлення дорівнює "ти хто" 
    або "хто ти" і це є відповіддю на повідомлення іншого користувача.
    """
    
    # 1. Визначення цільового користувача (той, на кого відповіли)
    target_user = message.reply_to_message.from_user
    
    # 2. Отримання даних цільового користувача:
    
    # Отримання карми:
    karma = store.get_karma(target_user.id, is_admin=False) 
    
    # Отримання статусу у чаті:
    chat_member = await bot.get_chat_member(
        chat_id=message.chat.id, 
        user_id=target_user.id
    )
    status = chat_member.status
    
    # Визначення ролі:
    role = "Адміністратор" if status in ["creator", "administrator"] else "Учасник"
    
    
    # 3. Формування відповіді:
    response_text = (
        f"<b>👤 Інформація про користувача {target_user.full_name}:</b>\n"
        f"📝 Ім'я: {target_user.full_name}\n"
        f"🏷 Статус: <b>{role}</b>\n"
        f"⚖️ Карма: <b>{karma}</b>\n"
        f"🆔 ID: <code>{target_user.id}</code>"
    )
    
    # 4. Надсилання відповіді:
    await message.reply(response_text, parse_mode=ParseMode.HTML)