from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import ContextTypes
from database.queries import (
    get_user,
    create_user,
    set_face_number,
    add_log,
    get_last_n_questions
)
from database.mocked_queries import (
    get_mocked_user_data,
    update_mocked_user_field
)
from rag.rag import classifier, get_answer_to_query, make_prompt
from chatgpt_md_converter import telegram_format

user_states = {}  # {user_id: {"state": ..., "field_to_edit": ...}}

FACE_CHOICE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("Физическое лицо", callback_data="prefix:Физическое лицо")],
    [InlineKeyboardButton("Юридическое лицо", callback_data="prefix:Юридическое лицо")]
])

PERSONAL_DATA_ENTRY_KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton("Изменить персональные данные")]
], resize_keyboard=True, one_time_keyboard=False)

PERSONAL_DATA_FIELD_CHOICES = InlineKeyboardMarkup([
    [InlineKeyboardButton("Имя", callback_data="edit:name")],
    [InlineKeyboardButton("Телефон", callback_data="edit:phone_number")],
    [InlineKeyboardButton("Дата рождения", callback_data="edit:date_of_birth")]
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    session = context.application.session

    # Check if user is already in the DB
    user = get_user(session, user_id)
    if user is None:
        await update.message.reply_text(
            "Здравствуйте, я робот-помощник.\nВыберите, пожалуйста, категорию вопроса:",
            reply_markup=FACE_CHOICE_KEYBOARD
        )
        user_states[user_id] = {"state": "awaiting_face_choice"}
    else:
        await update.message.reply_text(
            "Здравствуйте! Можете задать вопрос или изменить личные данные.",
            reply_markup=PERSONAL_DATA_ENTRY_KEYBOARD
        )
        user_states[user_id] = {"state": "awaiting_question"}

async def handle_prefix_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    face_type = query.data.split(":")[1]

    # Save new user in DB
    create_user(context.application.session, user_id, face_type)
    user_states[user_id] = {"state": "awaiting_question"}

    await query.delete_message()
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Спасибо. Теперь можете задать вопрос или изменить данные.",
        reply_markup=PERSONAL_DATA_ENTRY_KEYBOARD
    )

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    session = context.application.session
    mock_session = context.application.mock_session
    user = get_user(session, user_id)
    user_data = user_states.get(user_id)

    if not user or user_data.get("state") != "awaiting_question":
        return

    query = update.message.text.strip()

    if query == "Изменить персональные данные":
        await update.message.reply_text(
            "Выберите, что вы хотите изменить:",
            reply_markup=PERSONAL_DATA_FIELD_CHOICES
        )
        return

    OPENAI_KEY = context.application.OPENAI_KEY
    rag = context.application.rag

    label = classifier(OPENAI_KEY, query=query)

    if (
        label in (
            "2. Запрос на выдачу информации из личного кабинета",
            "3. Запрос на отправку информации в личный кабинет"
        )
        and user.face_number is None
    ):
        await update.message.reply_text("Пожалуйста, введите ваш номер лица:")
        user_states[user_id]["state"] = "awaiting_face_number"
        return

    history = get_last_n_questions(session, user_id)
    formatted_history = "\n".join([
        f"Классификация: {h.question_label}\nВопрос: {h.question}\nОтвет: {h.response}" for h in history
    ])

    system_prompt = make_prompt(face=user.face_type, history=formatted_history)
    answer = get_answer_to_query(query, system_prompt, rag)

    add_log(session, user_id, query, label, answer)
    escaped_text = telegram_format(answer)

    await update.message.reply_text(
        text=escaped_text,
        parse_mode="HTML",
        reply_markup=PERSONAL_DATA_ENTRY_KEYBOARD
    )

async def handle_user_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    session = context.application.session
    mock_session = context.application.mock_session
    state = user_states.get(user_id, {}).get("state")

    if state == "awaiting_face_number":
        set_face_number(session, user_id, int(text))
        user_states[user_id]["state"] = "awaiting_question"
        await update.message.reply_text("Спасибо! Теперь вы можете задать вопрос.")

    elif state == "awaiting_edit_field_value":
        field = user_states[user_id].get("field_to_edit")
        user = get_user(session, user_id)
        update_mocked_user_field(mock_session, user.face_number, field, text)
        user_states[user_id]["state"] = "awaiting_question"
        await update.message.reply_text("Данные успешно обновлены.", reply_markup=PERSONAL_DATA_ENTRY_KEYBOARD)

async def handle_field_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    field = query.data.split(":")[1]

    user_states[user_id] = {
        "state": "awaiting_edit_field_value",
        "field_to_edit": field
    }

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Отправьте новые данные:"
    )


async def main_message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Determine what to do based on current user state
    state = user_states.get(update.message.from_user.id, {}).get("state")

    if state in ("awaiting_face_number", "awaiting_edit_field_value"):
        await handle_user_reply(update, context)
    else:
        await handle_question(update, context)
