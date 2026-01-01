import os

# Telegram Bot Token
BOT_TOKEN = "8512207770:AAEKLtYEph7gleybGhF2lc7Gwq82Kj1yedM"

# Настройки модели
MODEL_NAME = "Qwen/Qwen-Image-Edit-2511"
TORCH_DTYPE = "bfloat16"

# Настройки генерации по умолчанию
DEFAULT_SETTINGS = {
    "num_inference_steps": 40,
    "guidance_scale": 1.0,
    "true_cfg_scale": 4.0,
    "negative_prompt": " ",
    "num_images_per_prompt": 1,
}

# Папка для временных файлов
TEMP_DIR = "temp_images"
os.makedirs(TEMP_DIR, exist_ok=True)
