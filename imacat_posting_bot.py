import os
import json
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Загрузка переменных окружения из .env файла
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Путь к файлу очереди
QUEUE_FILE = "video_queue.json"


def load_queue() -> list:
    """Загружает очередь video file_id из файла."""
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    return []


def save_queue(queue: list) -> None:
    """Сохраняет очередь video file_id в файл."""
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f)


async def handle_video(
        update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обрабатывает входящие видеофайлы от разрешённого пользователя."""
    if update.effective_user.id != USER_ID:
        return

    message = update.message
    video = message.video or message.document

    if not video:
        return

    file_id = video.file_id
    queue = load_queue()
    queue.append(file_id)
    save_queue(queue)

    await message.reply_text("Видео добавлено в очередь.")


async def post_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Публикует до 3 видео из очереди в указанный канал."""
    if update.effective_user.id != USER_ID:
        return

    queue = load_queue()
    if not queue:
        await update.message.reply_text("Нет видеофайлов для поста.")
        return

    files_to_post = queue[:3]
    for file_id in files_to_post:
        try:
            await context.bot.send_video(chat_id=CHANNEL_ID, video=file_id)
        except Exception as e:
            await update.message.reply_text(f"Ошибка при отправке видео: {e}")

    # Удаляем отправленные элементы из очереди
    queue = queue[3:]
    save_queue(queue)

    await update.message.reply_text("Видео отправлены в канал.")


async def count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает количество видео, находящихся в очереди."""
    if update.effective_user.id != USER_ID:
        return

    queue = load_queue()
    count = len(queue)
    await update.message.reply_text(f"Видео в очереди: {count}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветствие и указание времени запуска."""
    if update.effective_user.id != USER_ID:
        return

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    await update.message.reply_text(f"Бот активен. Время запуска: {now}")


async def marko(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Тестовая команда связи."""
    if update.effective_user.id != USER_ID:
        return

    await update.message.reply_text("Поло.")


def main() -> None:
    """Инициализация и запуск Telegram-бота."""
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("marko", marko))
    app.add_handler(CommandHandler("post_now", post_now))
    app.add_handler(CommandHandler("count", count))
    app.add_handler(MessageHandler(
        filters.VIDEO | filters.Document.VIDEO, handle_video)
    )

    print("Бот запущен. Готов к приёму и отправке видео.")
    app.run_polling()


if __name__ == '__main__':
    main()
