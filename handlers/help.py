import os
from typing import List, Tuple

import pandas as pd
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import settings
from keyboards import main_menu_kb, back_to_help_kb, faq_list_kb, faq_back_kb


help_router = Router()


def load_faq() -> List[Tuple[str, str]]:
    if not os.path.exists(settings.FAQ_FILE):
        raise FileNotFoundError(f"Файл FAQ не знайдено: {settings.FAQ_FILE}")
    df = pd.read_excel(settings.FAQ_FILE)
    df.columns = [c.strip().lower() for c in df.columns]
    if not {"ваше питання", "відповідь"}.issubset(df.columns):
        raise ValueError("У файлі відсутні колонки 'Ваше питання' або 'Відповідь'")
    df["ваше питання"] = df["ваше питання"].astype(str).str.strip()
    df["відповідь"] = df["відповідь"].astype(str).str.strip()
    df = df[(df["ваше питання"] != "") & (df["відповідь"] != "")]
    return list(df[["ваше питання", "відповідь"]].itertuples(index=False, name=None))


@help_router.message(Command(commands=["help"]))
async def open_panel(message: Message):
    await message.answer("<b>Що вас цікавить:</b>", reply_markup=main_menu_kb())


@help_router.callback_query(F.data == "back_help")
async def back_to_help(callback: CallbackQuery):
    await callback.message.edit_text("<b>Що вас цікавить:</b>", reply_markup=back_to_help_kb())
    await callback.answer()


@help_router.callback_query(F.data == "become_an_admin")
async def become_admin(callback: CallbackQuery):
    text = (
        "<b>👑 Як стати адміністратором:</b>\n\n"
        "Подайте заявку через офіційну Google форму:\n"
        f"<a href='{settings.ADMIN_APPLICATION_URL}'>📋 Подати заявку</a>"
    )
    await callback.message.answer(text, disable_web_page_preview=True)
    
    buttons = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@help_router.callback_query(F.data == "chat_rules")
async def chat_rules(callback: CallbackQuery):
    text = f"<b>❓ Ознайомитися з правилами:</b> <a href='{settings.CHAT_RULES_URL}'></a>"
    await callback.message.answer(text, disable_web_page_preview=True)
    
    buttons = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@help_router.callback_query(F.data == "users_commands")
async def users_commands(callback: CallbackQuery):
    text = (
        "📌 <b>Користувацькі команди:</b>\n\n"
        "🤖 <code>/gpt</code> <i>Промт</i> — запит до AI\n"
        "🚨 <code>/report</code> <i>Причина</i> — Викликати Адміністратора\n"
        "🚨 <code>/report</code> <i>Причина</i> (у відповіді на повідомлення) — скарга на користувача"
    )

    buttons = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@help_router.callback_query(F.data == "main_menu")
async def go_main_menu(callback: CallbackQuery):
    await callback.message.edit_text("<b>Що вас цікавить:</b>", reply_markup=main_menu_kb())
    await callback.answer()


@help_router.callback_query(F.data == "more_questions")
async def process_more_questions(callback: CallbackQuery):
    await callback.answer()
    try:
        faq_list = load_faq()
        questions = [q for q, _ in faq_list]
        await callback.message.edit_text(
            "<b>📋 Список питань:</b>\n\nОберіть, щоб побачити відповідь 👇",
            reply_markup=faq_list_kb(questions),
        )
    except Exception as e:
        await callback.message.edit_text(f"<b>❗ Помилка при завантаженні FAQ:</b> {str(e)}")


@help_router.callback_query(F.data.startswith("faq_"))
async def show_faq_answer(callback: CallbackQuery):
    await callback.answer()
    try:
        faq_list = load_faq()
        idx = int(callback.data.split("_")[1]) - 1
        if idx < 0 or idx >= len(faq_list):
            await callback.message.edit_text("<b>❗ Питання не знайдено.</b>")
            return
        question, answer = faq_list[idx]
        if answer.startswith("http://") or answer.startswith("https://"):
            text = f"<b>❓ {question}</b>\n\n✅ Можна дізнатися: <a href='{answer}'>тут</a>"
        else:
            text = f"<b>❓ {question}</b>\n\n✅ {answer}"
        await callback.message.edit_text(text, reply_markup=faq_back_kb())
    except Exception as e:
        await callback.message.edit_text(f"<b>❗ Помилка при завантаженні FAQ:</b> {str(e)}")