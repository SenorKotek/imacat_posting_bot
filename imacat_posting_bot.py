import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != USER_ID:
        return
    await update.message.reply_text("Приветули, я бот для постинга~ Мяу!")


async def marko(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != USER_ID:
        return
    await update.message.reply_text("Поло!")


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("marko", marko))
    print("Бот запущен и мяукает только тебе, ня~")
    app.run_polling()


if __name__ == '__main__':
    main()
