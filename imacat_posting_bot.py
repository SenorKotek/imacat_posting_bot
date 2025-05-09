import os
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

QUEUE_FILE = "video_queue.json"


def load_queue() -> list:
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    return []


def save_queue(queue: list) -> None:
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f)


async def handle_video(
        update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
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

    # Обновляем очередь
    queue = queue[3:]
    save_queue(queue)

    await update.message.reply_text("Видео отправлены в канал.")


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("post_now", post_now))
    app.add_handler(
        MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)
    )

    print("Бот готов: очередь на основе file_id.")
    app.run_polling()


if __name__ == '__main__':
    main()
