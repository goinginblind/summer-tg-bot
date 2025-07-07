from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

# Replace this with your bot token from BotFather
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm alive 😎")

# /echo command handler
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        response = ' '.join(context.args)
    else:
        response = "You didn't say anything to echo!"
    await update.message.reply_text(response)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("echo", echo))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
