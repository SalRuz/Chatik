import os
import random
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Включите логирование (опционально)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Укажите ваш токен бота от @BotFather
BOT_TOKEN = "8512207770:AAEKLtYEph7gleybGhF2lc7Gwq82Kj1yedM"

# Путь к папке с изображениями
IMAGE_FOLDER = Path("qwer")

async def jkl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not IMAGE_FOLDER.exists() or not IMAGE_FOLDER.is_dir():
        await update.message.reply_text("Папка 'qwer' не найдена.")
        return

    # Поддерживаемые расширения
    extensions = ('.png', '.jpg', '.jpeg')
    images = [f for f in IMAGE_FOLDER.iterdir() if f.suffix.lower() in extensions]

    if not images:
        await update.message.reply_text("В папке 'qwer' нет подходящих изображений.")
        return

    image_path = random.choice(images)
    try:
        with open(image_path, 'rb') as photo:
            await update.message.reply_photo(photo=photo)
    except Exception as e:
        await update.message.reply_text(f"Ошибка при отправке изображения: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("jkl", jkl))
    print("Бот запущен. Нажмите Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
