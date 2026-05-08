import ctypes
import os
import sys
import threading
import time

# Set DPI awareness before Tkinter or any GUI is initialized,
# so screen coordinates match actual pixel dimensions.
ctypes.windll.user32.SetProcessDPIAware()

from config import load_config, save_config
from screenshot_overlay import select_region
from clipboard_manager import set_image_to_clipboard
from ocr_engine import create_ocr_engine
from tray_app import TrayApp
from hotkey_listener import HotkeyListener
from pin_window import show_pin_window
from ocr_window import show_ocr_window

_tray = None
_ocr = None
_config = None


def _on_screenshot():
    """Called from the hotkey listener worker thread. Opens overlay, dispatches action."""
    try:
        image, action = select_region()
        if image is None or action is None:
            return  # user cancelled

        if action == "pin":
            show_pin_window(image)
        elif action == "ocr":
            show_ocr_window(image, _ocr)
        elif action == "copy":
            threading.Thread(target=_do_copy, args=(image,), daemon=True).start()
    except Exception as e:
        print(f"[ERROR] screenshot: {e}", file=sys.stderr)


def _do_copy(image):
    set_image_to_clipboard(image)
    if _config.get("notification_enabled", True):
        _tray.show_notification("截图已复制到剪贴板")


def main():
    global _tray, _ocr, _config

    _config = load_config()

    # Initialize OCR engine
    try:
        _ocr = create_ocr_engine(
            backend_name=_config["ocr_backend"],
            tesseract_cmd=_config.get("tesseract_path", ""),
            lang=_config.get("ocr_lang", "chi_sim+eng"),
        )
        print(f"OCR backend ready: {_ocr.name}")
    except Exception as e:
        print(f"WARNING: OCR not available ({e}). Image-only mode.", file=sys.stderr)
        _ocr = None

    # Setup tray
    def on_exit():
        if _listener:
            _listener.stop()

    _tray = TrayApp(on_screenshot=_on_screenshot, on_exit=on_exit)

    # Setup hotkey
    _listener = HotkeyListener(_config["hotkey"], _on_screenshot)

    print(f"Starting with hotkey: {_config['hotkey']}")
    print("Right-click tray icon for menu. Press Ctrl+C in terminal to stop.")

    try:
        _tray.run_detached()
        _listener.start()

        while _tray.running:
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        _listener.stop()
        _tray.stop()
        print("Bye.")


if __name__ == "__main__":
    main()
