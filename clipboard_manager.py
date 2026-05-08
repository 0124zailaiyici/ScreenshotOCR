import io
import ctypes
import struct
import win32clipboard
from PIL import Image


def _image_to_dib(image: Image.Image) -> bytes:
    """Convert PIL Image to CF_DIB format (BMP without the BITMAPFILEHEADER)."""
    output = io.BytesIO()
    image.convert("RGB").save(output, format="BMP")
    bmp_data = output.getvalue()

    # BMP file header is 14 bytes; the rest is DIB (BITMAPINFOHEADER + pixels)
    return bmp_data[14:]


def set_image_to_clipboard(image: Image.Image):
    """Copy a PIL Image to the Windows clipboard as CF_DIB."""
    dib = _image_to_dib(image)
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib)
    finally:
        win32clipboard.CloseClipboard()


def set_text_to_clipboard(text: str):
    """Copy text to the Windows clipboard as CF_UNICODETEXT."""
    if not text or not text.strip():
        return
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()


def set_both_to_clipboard(image: Image.Image, text: str):
    """Copy both image and text to clipboard. Image gets priority for paste."""
    dib = _image_to_dib(image)
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib)
        if text and text.strip():
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()
