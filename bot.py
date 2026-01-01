import asyncio
import logging
from io import BytesIO
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN, DEFAULT_SETTINGS
from image_processor import process_images, save_temp_image, cleanup_temp_file

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилище сессий пользователей
user_data = {}


def get_user_session(user_id: int) -> dict:
    """Получает или создаёт сессию пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {
            "images": [],
            "prompt": None,
            "settings": DEFAULT_SETTINGS.copy()
        }
    return user_data[user_id]


# ============ КОМАНДЫ ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие"""
    welcome = """
🎨 **Привет! Я бот для редактирования изображений**

Использую нейросеть **Qwen-Image-Edit-2511** от Alibaba.

📝 **Как пользоваться:**
1️⃣ Отправь 1-2 изображения
2️⃣ Напиши промпт (что хочешь сделать)
3️⃣ Получи результат!

🔧 **Команды:**
/start - Начать заново
/help - Помощь
/clear - Очистить изображения
/settings - Настройки

💡 **Примеры промптов:**
• "Add sunglasses to the person"
• "Make the background a sunset"
• "Combine both images into one scene"
    """
    
    user_data[update.effective_user.id] = {
        "images": [],
        "prompt": None,
        "settings": DEFAULT_SETTINGS.copy()
    }
    
    await update.message.reply_text(welcome, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    help_text = """
📚 **Инструкция**

🖼 **Изображения:**
• Отправь 1 или 2 картинки
• Форматы: JPG, PNG, WEBP

✏️ **Промпты:**
• Лучше писать на английском
• Будь конкретен в описании

⚙️ **Настройки:**
/set steps 50 — шаги генерации (10-100)
/set cfg 5.0 — сила промпта (1-10)

📌 **Примеры:**
• 1 фото: "Add a hat to the cat"
• 2 фото: "The dog from image 1 plays with cat from image 2"
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def clear_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очистить изображения"""
    session = get_user_session(update.effective_user.id)
    session["images"] = []
    session["prompt"] = None
    await update.message.reply_text("🗑 Изображения очищены!")


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать настройки"""
    session = get_user_session(update.effective_user.id)
    s = session["settings"]
    
    keyboard = [
        [
            InlineKeyboardButton(f"Steps: {s['num_inference_steps']}", callback_data="info_steps"),
            InlineKeyboardButton(f"CFG: {s['true_cfg_scale']}", callback_data="info_cfg"),
        ],
        [InlineKeyboardButton("🔄 Сбросить", callback_data="reset_settings")]
    ]
    
    text = f"""
⚙️ **Настройки:**

• Steps: `{s['num_inference_steps']}` (больше = качественнее)
• CFG: `{s['true_cfg_scale']}` (сила следования промпту)

Изменить: `/set steps 50` или `/set cfg 5.0`
    """
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def set_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить настройку"""
    session = get_user_session(update.effective_user.id)
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ Формат: `/set steps 50`", parse_mode='Markdown')
        return
    
    param = context.args[0].lower()
    value = context.args[1]
    
    try:
        if param == "steps":
            val = max(10, min(100, int(value)))
            session["settings"]["num_inference_steps"] = val
        elif param == "cfg":
            val = max(1.0, min(10.0, float(value)))
            session["settings"]["true_cfg_scale"] = val
        else:
            await update.message.reply_text(f"❌ Неизвестный параметр: {param}")
            return
        
        await update.message.reply_text(f"✅ {param} = {val}")
    except ValueError:
        await update.message.reply_text("❌ Неверное значение")


# ============ ОБРАБОТКА ИЗОБРАЖЕНИЙ ============

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение изображения"""
    session = get_user_session(update.effective_user.id)
    
    # Получаем файл
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
    elif update.message.document:
        file = await update.message.document.get_file()
    else:
        return
    
    # Скачиваем
    image_bytes = await file.download_as_bytearray()
    image = Image.open(BytesIO(image_bytes))
    
    # Максимум 2 изображения
    if len(session["images"]) >= 2:
        session["images"] = session["images"][1:]
    
    session["images"].append(image)
    count = len(session["images"])
    
    if count == 1:
        text = "📸 Изображение загружено!\n\n• Отправь ещё одно (опционально)\n• Или напиши промпт"
    else:
        text = f"📸 Загружено {count} изображения!\n\nТеперь напиши промпт"
    
    await update.message.reply_text(text)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение промпта"""
    session = get_user_session(update.effective_user.id)
    
    if not session["images"]:
        await update.message.reply_text("❌ Сначала загрузи изображение!")
        return
    
    prompt = update.message.text
    session["prompt"] = prompt
    
    keyboard = [[
        InlineKeyboardButton("✅ Генерировать", callback_data="generate"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel"),
    ]]
    
    await update.message.reply_text(
        f"📝 **Промпт:** {prompt}\n"
        f"🖼 **Изображений:** {len(session['images'])}\n\n"
        "Начать генерацию?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


# ============ CALLBACKS ============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    session = get_user_session(user_id)
    
    if query.data == "generate":
        await generate_image(query, session)
    elif query.data == "cancel":
        await query.edit_message_text("❌ Отменено")
    elif query.data == "reset_settings":
        session["settings"] = DEFAULT_SETTINGS.copy()
        await query.edit_message_text("✅ Настройки сброшены!")


async def generate_image(query, session: dict):
    """Генерация изображения"""
    await query.edit_message_text("⏳ Генерация... Это займёт 2-5 минут...")
    
    try:
        loop = asyncio.get_event_loop()
        
        result = await loop.run_in_executor(
            None,
            lambda: process_images(
                images=session["images"],
                prompt=session["prompt"],
                seed=0,
                num_steps=session["settings"]["num_inference_steps"],
                cfg_scale=session["settings"]["true_cfg_scale"]
            )
        )
        
        output_path = save_temp_image(result)
        
        with open(output_path, 'rb') as photo:
            await query.message.reply_photo(
                photo=photo,
                caption=f"✨ Готово!\n📝 {session['prompt']}"
            )
        
        cleanup_temp_file(output_path)
        await query.edit_message_text("✅ Генерация завершена!")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")


# ============ MAIN ============

def main():
    print("🤖 Запуск бота...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_images))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("set", set_setting))
    
    # Изображения
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.Document.IMAGE,
        handle_image
    ))
    
    # Текст
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text
    ))
    
    # Кнопки
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
