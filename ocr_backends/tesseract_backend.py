import os
import shutil
from PIL import Image, ImageFilter, ImageOps

from .base import OcrBackend

_COMMON_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
]


def _get_pytesseract():
    """Lazy import — pytesseract drags in pandas/pyarrow which may have NumPy issues."""
    import pytesseract
    return pytesseract


def _preprocess(image: Image.Image) -> Image.Image:
    """Prepare screenshot for OCR: upscale, grayscale, enhance contrast, denoise."""
    w, h = image.size

    # Upscale if too small (text needs ~30px height for good recognition)
    scale = 1.0
    if max(w, h) < 600:
        scale = 3.0
    elif max(w, h) < 1200:
        scale = 2.0

    if scale > 1.0:
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Convert to grayscale
    image = image.convert("L")

    # Increase contrast: stretch histogram to full range
    image = ImageOps.autocontrast(image, cutoff=2)

    # Light sharpen to make text edges crisper
    image = image.filter(ImageFilter.SHARPEN)

    return image


class TesseractBackend(OcrBackend):
    def __init__(self, tesseract_cmd="", lang="chi_sim+eng"):
        self._tesseract_cmd = tesseract_cmd
        self.lang = lang
        self._available = None
        self._tesseract_path = None

    def _find_tesseract(self):
        if self._tesseract_path:
            return self._tesseract_path
        if self._tesseract_cmd and os.path.exists(self._tesseract_cmd):
            self._tesseract_path = self._tesseract_cmd
            return self._tesseract_path
        for p in _COMMON_TESSERACT_PATHS:
            if os.path.exists(p):
                self._tesseract_path = p
                return p
        found = shutil.which("tesseract")
        if found:
            self._tesseract_path = found
            return found
        return None

    @property
    def name(self) -> str:
        return "Tesseract-OCR"

    def is_available(self) -> bool:
        if self._available is None:
            self._available = self._find_tesseract() is not None
        return self._available

    def recognize(self, image: Image.Image) -> str:
        if not self.is_available():
            raise RuntimeError("Tesseract is not installed or not found in PATH")

        pytesseract = _get_pytesseract()
        pytesseract.pytesseract.tesseract_cmd = self._find_tesseract()

        processed = _preprocess(image)

        # OEM 1 = LSTM only (faster, more accurate for modern Tesseract 4+)
        # PSM 3 = fully automatic page segmentation (best for mixed screenshots)
        config = "--oem 1 --psm 3"
        text = pytesseract.image_to_string(processed, lang=self.lang, config=config)
        return text.strip()
