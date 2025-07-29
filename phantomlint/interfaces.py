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

class RendererElement(ABC):
    @abstractmethod
    def render_image(self) -> Image.Image:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass
    
class Renderer(ABC):
    @abstractmethod
    def get_elements(self, path: Path) -> List[RendererElement]:
        pass

