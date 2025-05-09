import os
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

QUEUE_FILE = "video_queue.json"
schedule_enabled = False
scheduled_jobs = []
scheduler = AsyncIOScheduler()


def load_queue() -> list:
    """Загружает очередь из файла JSON, если он существует."""
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    return []


def save_queue(queue: list) -> None:
    """Сохраняет текущую очередь в JSON-файл."""
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f)


async def handle_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обрабатывает входящее видео от пользователя и добавляет его в очередь,
    если такого видео ещё нет (по unique_id)."""
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
    """Публикует заданное количество видео из очереди в канал.
    Если randomize=True — выбирает случайные видео."""
    if update.effective_user.id != USER_ID:
        return

    await do_posting(context, count=count, randomize=randomize)


async def do_posting(
        context: ContextTypes.DEFAULT_TYPE, count: int, randomize: bool = False
) -> None:
    queue = load_queue()
    if not queue:
        await context.bot.send_message(
            chat_id=USER_ID, text="Нет видеофайлов для поста."
        )
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
            await context.bot.send_message(
                chat_id=USER_ID, text=f"Ошибка при отправке видео: {e}"
            )

    save_queue(queue)
    await context.bot.send_message(
        chat_id=USER_ID,
        text=f"Отправлено {len(files_to_post)} видео в канал."
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
    """Команда /count — показывает количество видео в очереди."""
    if update.effective_user.id != USER_ID:
        return

    queue = load_queue()
    await update.message.reply_text(f"Видео в очереди: {len(queue)}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start — выводит текущее время запуска бота."""
    if update.effective_user.id != USER_ID:
        return

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    await update.message.reply_text(f"Бот активен. Время запуска: {now}")


async def marko(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /marko — проверка связи, отвечает 'Поло.'"""
    if update.effective_user.id != USER_ID:
        return

    await update.message.reply_text("Поло.")


async def schedule_mode(
        update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Включает автоматический режим постинга с планированием на день."""
    global schedule_enabled
    if update.effective_user.id != USER_ID:
        return

    schedule_enabled = True
    scheduler.add_job(
        plan_daily_posts, "cron", hour=8, minute=0, id="daily_schedule"
    )
    await update.message.reply_text(
        "Автоматический режим включён."
        "Расписание будет создаваться ежедневно в 08:00."
    )


async def schedule_mode_off(
        update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Отключает автоматический режим постинга."""
    global schedule_enabled
    if update.effective_user.id != USER_ID:
        return

    schedule_enabled = False
    scheduler.remove_job("daily_schedule")
    for job in scheduled_jobs:
        try:
            scheduler.remove_job(job)
        except Exception:
            pass
    scheduled_jobs.clear()
    await update.message.reply_text("Автоматический режим выключен.")


async def plan_daily_posts():
    """Планирует посты на текущий день: каждые 2–3 часа с 8:00 до 23:00."""
    global scheduled_jobs
    scheduled_jobs.clear()

    start_time = datetime.now().replace(
        hour=8, minute=0, second=0, microsecond=0
    )
    end_time = datetime.now().replace(
        hour=23, minute=0, second=0, microsecond=0
    )

    post_times = []
    current_time = start_time
    while current_time < end_time:
        interval = timedelta(hours=random.randint(2, 3))
        current_time += interval
        if current_time < end_time:
            post_times.append(current_time)

    # Отправка расписания хозяину
    times_list = "\n".join(t.strftime("%H:%M") for t in post_times)
    queue_size = len(load_queue())
    await scheduler._context.bot.send_message(
        chat_id=USER_ID,
        text=(
            f"Сегодняшнее расписание постов:\n{times_list}\n"
            f"Видео в очереди: {queue_size}"
        )
    )

    for t in post_times:
        job_id = f"autopost_{t.strftime('%H%M')}"
        scheduler.add_job(
            func=do_posting,
            trigger="date",
            run_date=t,
            kwargs={
                "context": scheduler._context,
                "count": random.randint(2, 4),
                "randomize": False
            },
            id=job_id
        )
        scheduled_jobs.append(job_id)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /status — показывает состояние очереди и расписания."""
    if update.effective_user.id != USER_ID:
        return

    queue = load_queue()
    status_lines = [
        f"Автопостинг: {'ВКЛЮЧЕН' if schedule_enabled else 'выключен'}",
        f"Видео в очереди: {len(queue)}"
    ]

    if schedule_enabled and scheduled_jobs:
        times = [
            scheduler.get_job(job_id).next_run_time.strftime("%H:%M")
            for job_id in scheduled_jobs
            if scheduler.get_job(job_id)
        ]
        status_lines.append("Оставшиеся публикации сегодня:")
        status_lines.extend(times)
    elif schedule_enabled:
        status_lines.append("На сегодня публикации не запланированы.")

    await update.message.reply_text("\n".join(status_lines))


async def set_my_commands(app):
    """Регистрирует команды для Telegram-подсказки через /"""
    await app.bot.set_my_commands([
        BotCommand("start", "Показать время запуска"),
        BotCommand("marko", "Проверка связи"),
        BotCommand("count", "Сколько видео в очереди"),
        BotCommand("post_now", "Постить 3 видео"),
        BotCommand("post_now_five", "Постить 5 видео"),
        BotCommand("post_now_random", "Постить 2–5 случайных видео"),
        BotCommand("schedule_mode", "Включить автоматический режим"),
        BotCommand("schedule_mode_off", "Выключить автоматический режим"),
        BotCommand("status", "Показать статус автопостинга и очереди"),
    ])


async def on_startup(app):
    await set_my_commands(app)
    scheduler._context = app.bot
    scheduler.start()


def main() -> None:
    """Инициализация и запуск Telegram-бота с регистрацией команд."""
    app = ApplicationBuilder().token(TOKEN).post_init(on_startup).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("marko", marko))
    app.add_handler(CommandHandler("count", count))
    app.add_handler(CommandHandler("post_now", post_now))
    app.add_handler(CommandHandler("post_now_random", post_now_random))
    app.add_handler(CommandHandler("post_now_five", post_now_five))
    app.add_handler(CommandHandler("schedule_mode", schedule_mode))
    app.add_handler(CommandHandler("schedule_mode_off", schedule_mode_off))
    app.add_handler(
        MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)
    )
    app.add_handler(CommandHandler("status", status))

    print("Бот запущен. Команды Telegram зарегистрированы.")
    app.run_polling()


if __name__ == '__main__':
    main()
