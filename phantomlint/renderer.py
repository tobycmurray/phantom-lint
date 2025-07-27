from phantomlint.interfaces import Renderer
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from PIL import Image
import pymupdf  # PyMuPDF
from pdf2image import convert_from_path

SUPPORTED_FILETYPES=["pdf"]
def renderer_for(path: Path, precise: bool = False) -> Renderer:
    if path.suffix.lower() == ".pdf":
        if precise:
            return LocalizedPDFRenderer()
        else:
            return PDFRenderer()
    else:
        return None

class PDFRenderer(Renderer):
    def extract_text(self, path: Path) -> str:
        with pymupdf.open(path) as doc:
            return "\n".join(page.get_text() for page in doc)

    def render_images(self, path: Path, dpi: int = 300) -> List[Image.Image]:
        return convert_from_path(str(path), dpi=dpi)

class LocalizedPDFRenderer(Renderer):
    def extract_text(self, pdf_path: Path) -> str:
        doc = pymupdf.open(pdf_path)
        return "\n".join(page.get_text() for page in doc)

    def render_images(self, pdf_path: Path, dpi: int) -> List[Image.Image]:
        zoom = dpi / 72  # PDF default resolution is 72 DPI
        all_crops = []

        doc = pymupdf.open(pdf_path)

        for page_number, page in enumerate(doc, start=1):
            # Render full page
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            for block in page.get_text("dict")["blocks"]:
                if block["type"] != 0:  # Only text blocks
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        x0, y0, x1, y1 = [int(coord * zoom) for coord in span["bbox"]]

                        # Clamp coordinates to image bounds
                        x0 = max(0, min(x0, image.width))
                        x1 = max(0, min(x1, image.width))
                        y0 = max(0, min(y0, image.height))
                        y1 = max(0, min(y1, image.height))

                        if x1 > x0 and y1 > y0:
                            crop = image.crop((x0, y0, x1, y1))
                            all_crops.append(crop)

        return all_crops
            
