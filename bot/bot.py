from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from rag.rag import make_rag
from bot.handlers import (
    start,
    handle_prefix_choice,
    handle_question,
    handle_user_reply,
    handle_field_choice,
)

def run_bot():
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OPENAI_KEY = os.getenv("OPENAI_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    MOCKED_DB_URL = os.getenv("MOCKED_DB_URL")

    # MAIN DB
    engine_main_db = create_engine(DATABASE_URL)
    Session_main_db = sessionmaker(bind=engine_main_db)
    session_main_db = Session_main_db()

    # MOCKED DB
    engine_mock_db = create_engine(MOCKED_DB_URL)
    Session_mock_db = sessionmaker(bind=engine_mock_db)
    session_mock_db = Session_mock_db()

    # RAG init
    rag = make_rag(key=OPENAI_KEY)

    # Telegram bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.rag = rag
    app.session = session_main_db
    app.mock_session = session_mock_db
    app.OPENAI_KEY = OPENAI_KEY

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_prefix_choice, pattern="^prefix:"))
    app.add_handler(CallbackQueryHandler(handle_field_choice, pattern="^edit:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_reply))

    print("Bot is running...")
    app.run_polling()
