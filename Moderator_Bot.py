import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import settings  # config.py має бути в корені проекту

# --- Імпорти роутерів ---
from handlers import (
    moderation_router,
    report_router,
    karma_router,
)

from handlers.user_info import user_info_router
from handlers.ai_ask import ai_ask_router
from handlers.text_moderation import text_moderation_router
from handlers.offtop_router import offtop_router
from handlers.wallet import wallet_router
from handlers.vip_router import vip_router  # якщо є VIP функціонал

# --- Data Store ---
from data_store import DataStore


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_router(moderation_router)       # 1
    dp.include_router(text_moderation_router)  # 2
    dp.include_router(offtop_router)           # 3
    dp.include_router(report_router)           # 4
    dp.include_router(vip_router)              # 5
    dp.include_router(wallet_router)           # 6
    dp.include_router(user_info_router)        # 7
    dp.include_router(karma_router)            # 8
    dp.include_router(ai_ask_router)           # 9

    # --- Очищення черги ---
    await bot.delete_webhook(drop_pending_updates=True)

    # --- DataStore (shared between handlers) ---
    dp["store"] = DataStore()

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.warning("⚠️ Бота зупинено користувачем.")
    except Exception as e:
        logging.error(f"❌ Помилка при запуску бота: {e}")


if __name__ == "__main__":
    asyncio.run(main())
