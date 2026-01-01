import os
import torch
from PIL import Image
from typing import List
import uuid

_pipeline = None


def get_pipeline():
    """Загружает модель один раз и кэширует"""
    global _pipeline
    
    if _pipeline is None:
        print("🔄 Загрузка Qwen-Image-Edit-2511...")
        from diffusers import QwenImageEditPlusPipeline
        from config import MODEL_NAME
        
        _pipeline = QwenImageEditPlusPipeline.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.bfloat16
        )
        _pipeline.to('cuda')
        _pipeline.set_progress_bar_config(disable=None)
        print("✅ Модель загружена!")
    
    return _pipeline


def process_images(
    images: List[Image.Image],
    prompt: str,
    seed: int = 0,
    num_steps: int = 40,
    cfg_scale: float = 4.0
) -> Image.Image:
    """Обрабатывает изображения через Qwen-Image-Edit"""
    pipeline = get_pipeline()
    
    # Конвертируем в RGB
    images = [img.convert('RGB') for img in images]
    
    inputs = {
        "image": images,
        "prompt": prompt,
        "generator": torch.manual_seed(seed),
        "true_cfg_scale": cfg_scale,
        "negative_prompt": " ",
        "num_inference_steps": num_steps,
        "guidance_scale": 1.0,
        "num_images_per_prompt": 1,
    }
    
    with torch.inference_mode():
        output = pipeline(**inputs)
        return output.images[0]


def save_temp_image(image: Image.Image) -> str:
    """Сохраняет изображение во временную папку"""
    from config import TEMP_DIR
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(TEMP_DIR, filename)
    image.save(filepath)
    return filepath


def cleanup_temp_file(filepath: str):
    """Удаляет временный файл"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Ошибка удаления: {e}")
