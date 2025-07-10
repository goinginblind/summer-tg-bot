import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from rag.rag import make_rag
from bot.handlers import start, handle_prefix_choice, go_back, handle_question, ask_another

def run_bot():
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OPENAI_KEY = os.getenv("OPENAI_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Запуск ДБ
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Запуск РАГ
    rag = make_rag(key=OPENAI_KEY)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # Чтоб хэндлеры могли доставать раг и дб
    app.rag = rag
    app.session = session
    app.OPENAI_KEY = OPENAI_KEY

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_prefix_choice, pattern="^prefix:"))
    app.add_handler(CallbackQueryHandler(go_back, pattern="^go_back$"))
    app.add_handler(CallbackQueryHandler(ask_another, pattern="^ask_another$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))

    print("Bot is running...")
    app.run_polling()
