import json
import os
import sys


DEFAULT_CONFIG = {
    "hotkey": "<ctrl>+<shift>+a",
    "ocr_backend": "tesseract",
    "ocr_lang": "chi_sim+eng",
    "auto_copy_text": True,
    "auto_copy_image": True,
    "notification_enabled": True,
    "tesseract_path": "",
}


def _get_config_dir():
    """Config lives next to the executable (or source code), not in C:\\Users."""
    if getattr(sys, "frozen", False):
        # PyInstaller: use the dir containing the .exe
        return os.path.dirname(sys.executable)
    else:
        # Running from source: use the project directory
        return os.path.dirname(os.path.abspath(__file__))


CONFIG_PATH = os.path.join(_get_config_dir(), "screenshot_ocr_config.json")


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
