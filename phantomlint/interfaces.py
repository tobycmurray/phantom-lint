from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple
from PIL import Image
from phantomlint.word_spans import Span

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
    def analyze(self, bad_phrases: List[str], phrases: List[str]) -> List[Tuple[str, List[Span]]]:
        pass

class Differ(ABC):
    @abstractmethod
    def find_hidden_spans(self, full_phrase: str, spans: List[Span], ocr_phrases: List[str]) -> List[Span]:
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

