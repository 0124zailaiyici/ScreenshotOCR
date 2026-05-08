import os
import threading
from PIL import Image, ImageDraw
import pystray

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_ICON_PATH = os.path.join(_ASSETS_DIR, "tray_icon.png")


def _generate_icon():
    """Generate a simple 32x32 camera/scissor icon if none exists."""
    if not os.path.exists(_ASSETS_DIR):
        os.makedirs(_ASSETS_DIR, exist_ok=True)

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Body: rounded rectangle in dark gray
    draw.rounded_rectangle([4, 12, 52, 56], radius=6, fill="#4A90D9")

    # Inner screen highlight
    draw.rounded_rectangle([10, 18, 46, 44], radius=3, fill="#1A1A2E")

    # Dashed selection rectangle (white)
    dash_len = 6
    gap = 4
    rect_x1, rect_y1, rect_x2, rect_y2 = 18, 24, 38, 38
    # top edge
    for x in range(rect_x1, rect_x2, dash_len + gap):
        draw.line([(x, rect_y1), (min(x + dash_len, rect_x2), rect_y1)], fill="white", width=1)
    # bottom edge
    for x in range(rect_x1, rect_x2, dash_len + gap):
        draw.line([(x, rect_y2), (min(x + dash_len, rect_x2), rect_y2)], fill="white", width=1)
    # left edge
    for y in range(rect_y1, rect_y2, dash_len + gap):
        draw.line([(rect_x1, y), (rect_x1, min(y + dash_len, rect_y2))], fill="white", width=1)
    # right edge
    for y in range(rect_y1, rect_y2, dash_len + gap):
        draw.line([(rect_x2, y), (rect_x2, min(y + dash_len, rect_y2))], fill="white", width=1)

    # Small crosshair circle in center
    cx, cy = 28, 31
    draw.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill="#00BFFF")

    img.save(_ICON_PATH, "PNG")
    return img


def get_icon():
    if not os.path.exists(_ICON_PATH):
        _generate_icon()
    return Image.open(_ICON_PATH)


class TrayApp:
    def __init__(self, on_screenshot=None, on_exit=None):
        self._on_screenshot = on_screenshot
        self._on_exit = on_exit
        self._running = False
        self.icon = None

    @property
    def running(self):
        return self._running

    def _create_icon(self):
        menu = pystray.Menu(
            pystray.MenuItem("截图", self._trigger_screenshot, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._do_exit),
        )
        self.icon = pystray.Icon("screenshot_ocr", get_icon(), "截图 OCR", menu)

    def _trigger_screenshot(self):
        if self._on_screenshot:
            threading.Thread(target=self._on_screenshot, daemon=True).start()

    def _do_exit(self):
        self._running = False
        if self._on_exit:
            self._on_exit()
        if self.icon:
            self.icon.stop()

    def show_notification(self, text: str):
        if self.icon:
            self.icon.notify(text, title="截图 OCR")

    def run_detached(self):
        self._create_icon()
        self._running = True
        self.icon.run_detached()

    def stop(self):
        self._running = False
        if self.icon:
            self.icon.stop()
