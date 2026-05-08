import json
import os

DEFAULT_CONFIG = {
    "hotkey": "<ctrl>+<shift>+a",
    "ocr_backend": "tesseract",
    "ocr_lang": "chi_sim+eng",
    "auto_copy_text": True,
    "auto_copy_image": True,
    "notification_enabled": True,
    "tesseract_path": "",
}

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".screenshot_ocr_config.json")


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
