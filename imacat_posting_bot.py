import os
import json
import random
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, BotCommand
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
    file_unique_id = video.file_unique_id

    queue = load_queue()
    if any(item["unique_id"] == file_unique_id for item in queue):
        await message.reply_text("Это видео уже в очереди.")
        return

    queue.append({"id": file_id, "unique_id": file_unique_id})
    save_queue(queue)

    await message.reply_text("Видео добавлено в очередь.")


async def post_videos(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    count: int, randomize: bool = False
) -> None:
    if update.effective_user.id != USER_ID:
        return

    queue = load_queue()
    if not queue:
        await update.message.reply_text("Нет видеофайлов для поста.")
        return

    if randomize:
        sample_size = min(count, len(queue))
        files_to_post = random.sample(queue, sample_size)
        queue = [item for item in queue if item not in files_to_post]
    else:
        files_to_post = queue[:count]
        queue = queue[count:]

    for item in files_to_post:
        try:
            await context.bot.send_video(chat_id=CHANNEL_ID, video=item["id"])
        except Exception as e:
            await update.message.reply_text(f"Ошибка при отправке видео: {e}")

    save_queue(queue)
    await update.message.reply_text(
        f"Отправлено {len(files_to_post)} видео в канал."
    )


async def post_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await post_videos(update, context, count=3, randomize=False)


async def post_now_random(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await post_videos(
        update, context, count=random.randint(2, 5), randomize=True
    )


async def post_now_five(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await post_videos(update, context, count=5, randomize=False)


async def count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != USER_ID:
        return

    queue = load_queue()
    await update.message.reply_text(f"Видео в очереди: {len(queue)}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != USER_ID:
        return

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    await update.message.reply_text(f"Бот активен. Время запуска: {now}")


async def marko(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != USER_ID:
        return

    await update.message.reply_text("Поло.")


async def set_my_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Показать время запуска"),
        BotCommand("marko", "Проверка связи"),
        BotCommand("count", "Сколько видео в очереди"),
        BotCommand("post_now", "Постить 3 видео"),
        BotCommand("post_now_five", "Постить 5 видео"),
        BotCommand("post_now_random", "Постить 2–5 случайных видео"),
    ])


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("marko", marko))
    app.add_handler(CommandHandler("count", count))
    app.add_handler(CommandHandler("post_now", post_now))
    app.add_handler(CommandHandler("post_now_random", post_now_random))
    app.add_handler(CommandHandler("post_now_five", post_now_five))
    app.add_handler(
        MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)
    )

    app.run_async(set_my_commands(app))

    print("Бот запущен. Команды Telegram зарегистрированы.")
    app.run_polling()


if __name__ == '__main__':
    main()
