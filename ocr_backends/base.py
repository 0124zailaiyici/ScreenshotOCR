from abc import ABC, abstractmethod
from PIL import Image


class OcrBackend(ABC):
    @abstractmethod
    def recognize(self, image: Image.Image) -> str:
        """Return recognized text from a PIL Image."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the backend is ready to use."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name."""
        ...
