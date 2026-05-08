from ocr_backends.base import OcrBackend
from ocr_backends.tesseract_backend import TesseractBackend

BACKENDS = {
    "tesseract": TesseractBackend,
}


def create_ocr_engine(backend_name="tesseract", **kwargs) -> OcrBackend:
    backend_cls = BACKENDS.get(backend_name)
    if backend_cls is None:
        raise ValueError(f"Unknown OCR backend: {backend_name}")

    backend = backend_cls(**kwargs)
    if not backend.is_available():
        raise RuntimeError(
            f"OCR backend '{backend_name}' is not available. "
            "Please install Tesseract-OCR from: "
            "https://github.com/UB-Mannheim/tesseract/wiki"
        )
    return backend


def get_available_backends() -> list[str]:
    available = []
    for name, backend_cls in BACKENDS.items():
        try:
            b = backend_cls()
            if b.is_available():
                available.append(name)
        except Exception:
            pass
    return available
