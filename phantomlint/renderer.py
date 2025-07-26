from phantomlint.interfaces import Renderer
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from PIL import Image
import fitz  # PyMuPDF
from pdf2image import convert_from_path

SUPPORTED_FILETYPES=["pdf"]
def renderer_for(path: Path) -> Renderer:
    if path.suffix.lower() == ".pdf":
        return PDFRenderer()
    else:
        return None

class PDFRenderer(Renderer):
    def extract_text(self, path: Path) -> str:
        with fitz.open(path) as doc:
            return "\n".join(page.get_text() for page in doc)

    def render_images(self, path: Path, dpi: int = 300) -> List[Image.Image]:
        return convert_from_path(str(path), dpi=dpi)

            
