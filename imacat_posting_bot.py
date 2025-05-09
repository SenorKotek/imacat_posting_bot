import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение токена и разрешённого user_id
TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /start. Доступна только авторизованному пользователю.
    """
    if update.effective_user.id != USER_ID:
        return
    await update.message.reply_text("Бот активен. Готов к работе.")


async def marko(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /marko. Проверка связи.
    """
    if update.effective_user.id != USER_ID:
        return
    await update.message.reply_text("Поло.")


def main() -> None:
    """
    Инициализация и запуск Telegram-бота.
    """
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("marko", marko))

    print("Бот запущен. Доступ разрешён только одному пользователю.")
    app.run_polling()


if __name__ == '__main__':
    main()
