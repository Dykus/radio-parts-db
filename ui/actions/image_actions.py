# ui/actions/image_actions.py
import uuid
import shutil
import logging
from pathlib import Path
from config import DATA_DIR

logger = logging.getLogger(__name__)

class ImageActions:
    @staticmethod
    def process_image(src_path, part_id, index):
        images_dir = DATA_DIR / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        dest_name = f"part_{part_id}_img_{index}_{uuid.uuid4().hex[:8]}.webp"
        dest_path = images_dir / dest_name
        try:
            from PIL import Image
            img = Image.open(src_path)
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            max_size = 1024
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            img.save(dest_path, 'WEBP', quality=85, optimize=True)
            return dest_name
        except Exception as e:
            logger.error(f"Ошибка обработки изображения {src_path}: {e}")
            fallback_name = f"part_{part_id}_img_{index}_{Path(src_path).name}"
            fallback_path = images_dir / fallback_name
            shutil.copy2(src_path, fallback_path)
            return fallback_name

    @staticmethod
    def save_images_for_part(db, part_id, image_files):
        result = {}
        for i, file_path in enumerate(image_files[:3]):
            if file_path and Path(file_path).exists():
                filename = ImageActions.process_image(file_path, part_id, i+1)
                if i == 0:
                    result['image_path'] = filename
                else:
                    result[f'image_path_{i+1}'] = filename
        return result