from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database.queries import add_log, get_last_n_questions
from rag.rag import (
    classifier,
    get_answer_to_query,
    human_query_to_gpt_prompt,
    make_prompt,
)
from chatgpt_md_converter import telegram_format

# Юзер стейт: {user_id: {"face": "Физическое лицо", "query": "awaiting_question"}}
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

    # Промпт для юзера чтоб вбил текстовый запрос
    back_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="go_back")]
    ])
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Напишите, пожалуйста, ваш вопрос или нажмите кнопку, чтобы выбрать другую категорию:",
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
    session = context.application.session
    rag = context.application.rag
    OPENAI_KEY = context.application.OPENAI_KEY

    if not user_data or user_data.get("state") != "awaiting_question":
        return

    face = user_data["prefix"]
    query = update.message.text

    user_history_list = get_last_n_questions(session=session, user_id=user_id, n=10)
    user_history = ""
    for i in range(len(user_history_list)):
        user_history += f"Классификация вопроса: {user_history_list[i].question_label}\nВопрос: {user_history_list[i].question}\nОтвет: {user_history_list[i].response}"

    label = classifier(OPENAI_KEY, query=query)
    query = human_query_to_gpt_prompt(OPENAI_KEY, query=query)
    
    # Парс вопроса и истории в ллм и получение ответа
    system_prompt=make_prompt(face=face, history=user_history)
    answer = get_answer_to_query(query, system_prompt, rag)

    # Лог в ДБ
    add_log(session=session, user_id=user_id, question=query, response=answer, question_label=label)

    # Отправляем юзеру
    escaped_text = telegram_format(answer)  # Тут эскейп маркдауна

    await update.message.reply_text(
        text=escaped_text,
        parse_mode="HTML",
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
