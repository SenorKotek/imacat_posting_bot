FROM python:3.11-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копируем файлы
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запуск бота
CMD ["python", "imacat_posting_bot.py"]
