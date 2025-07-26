from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from PIL import Image

class OCREngine(ABC):
    @abstractmethod
    def extract_text(self, images: List[Image.Image]) -> str:
        pass

class Splitter(ABC):
    @abstractmethod
    def split(self, text: str) -> List[str]:
        pass

class Analyzer(ABC):
    @abstractmethod
    def analyze(self, bad_phrases: List[str], phrases: List[str]) -> List[str]:
        pass

class Differ(ABC):
    @abstractmethod
    def find_hidden_phrases(self, full_phrases: List[str], ocr_phrases: List[str]) -> List[str]:
        pass
    
class Renderer(ABC):
    @abstractmethod
    def extract_text(self, path: Path) -> str:
        pass

    @abstractmethod
    def render_images(self, path: Path, dpi: int) -> List[Image.Image]:
        pass
