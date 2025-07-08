from dotenv import load_dotenv
import os
from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)


# Юзер стейт: {user_id: {"prefix": "Физическое лицо", "state": "awaiting_question"}}
# Его в млучае чего можно заменить на ДБ или ДБ + редис если вдруг внезапно 
# кому-то на кой-то хер понадобится делать это всё с нескольких серверов
user_states = {}

FACE_CHOICE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("Физическое лицо", callback_data="prefix:Физическое лицо")],
    [InlineKeyboardButton("Юридическое лицо", callback_data="prefix:Юридическое лицо")]
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте, я робот-помощник.\nВыберите, пожалуйста, категорию вопроса:",
        reply_markup=FACE_CHOICE_KEYBOARD
    )

async def handle_prefix_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prefix = query.data.split(":")[1]
    user_id = query.from_user.id
    user_states[user_id] = {"prefix": prefix, "state": "awaiting_question"}

    # Удаляет предыдущее сообщение с кнопками для лиц
    await query.delete_message()

    # Пропмпт для юзера чтоб вбил текстовый запрос
    back_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="go_back")]
    ])
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Напишите, пожалуйста, ваш запрос:",
        reply_markup=back_button
    )

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.delete_message()
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Пожалуйста, выберите категорию вопроса:",
        reply_markup=FACE_CHOICE_KEYBOARD
    )

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data = user_states.get(user_id)

    if not user_data or user_data.get("state") != "awaiting_question":
        return

    face = user_data["prefix"]
    query = update.message.text

    full_prompt = f"{face}: {query}"
    
    # ВОТ ТУТ БУДЕТ ПАРС В ЛЛМ И ПОЛУЧЕНИЕ ОТВЕТА

    response = f"[Ваш ответ: {full_prompt}]" # Это плейсхолдееер

    # Отправляем юзеру
    await update.message.reply_text(
        text=response,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Задать другой вопрос", callback_data="ask_another")]
        ])
    )

async def ask_another(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Выберите, пожалуйста:",
        reply_markup=FACE_CHOICE_KEYBOARD
    )

if __name__ == '__main__':
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_prefix_choice, pattern="^prefix:"))
    app.add_handler(CallbackQueryHandler(go_back, pattern="^go_back$"))
    app.add_handler(CallbackQueryHandler(ask_another, pattern="^ask_another$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))

    print("Bot is running...")
    app.run_polling()
