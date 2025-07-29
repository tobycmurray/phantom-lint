from phantomlint.interfaces import Renderer, RendererElement
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from PIL import Image
import pymupdf  # PyMuPDF
from pdf2image import convert_from_path
import logging

log = logging.getLogger(__name__)

SUPPORTED_FILETYPES=["pdf"]
def renderer_for(path: Path) -> Renderer:
    if path.suffix.lower() == ".pdf":
        return PDFRenderer()
    else:
        return None

class PDFRendererElement(RendererElement):
    def __init__(self, page_number, page, block):
        self.page = page
        self.page_number = page_number
        self.block = block

    def get_text(self) -> str:
        block_text = ""
        for line in self.block.get("lines", []):
            for span in line.get("spans", []):
                block_text += span["text"]
            block_text += "\n"
        return block_text
        
    def render_image(self, dpi: int) -> Image.Image:
        zoom = dpi / 72.0  # PDF default resolution is 72 DPI
        mat = pymupdf.Matrix(zoom, zoom)
        pix = self.page.get_pixmap(matrix=mat)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        x0, y0, x1, y1 = [int(coord * zoom) for coord in self.block["bbox"]]

        # Clamp coordinates within image bounds
        image_width, image_height = image.size
        x0 = max(0, min(x0, image_width))
        x1 = max(0, min(x1, image_width))
        y0 = max(0, min(y0, image_height))
        y1 = max(0, min(y1, image_height))

        cropped_image = image.crop((x0, y0, x1, y1))
        return cropped_image
    
class PDFRenderer(Renderer):
    def get_elements(self, path: Path) -> List[PDFRendererElement]:
        elements = []
        doc = pymupdf.open(path)

        for page_number, page in enumerate(doc, start=1):
            # if we don't find any lines on the page, fall back to using whole-page rendering
            found_lines=False
            for block in page.get_text("dict")["blocks"]:
                if block["type"] != 0:  # Only text blocks
                    continue
                if block.get("lines", []) != []:
                    e = PDFRendererElement(page_number, page, block)
                    elements.append(e)
                    found_lines=True
            if not found_lines:
                log.info(f"No text lines found on page {page_number}. Using whole-page renderer for that page")
                e = PDFPageRendererElement(page_number, page)
                elements.append(e)
                
        return elements


class PDFPageRendererElement(RendererElement):
    def __init__(self, page_number, page):
        self.page = page
        self.page_number = page_number

    def get_text(self) -> str:
        return self.page.get_text("text")

    def render_image(self, dpi: int) -> Image.Image:
        zoom = dpi / 72.0  # PDF default resolution is 72 DPI
        mat = pymupdf.Matrix(zoom, zoom)
        pix = self.page.get_pixmap(matrix=mat)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return image

# each element is just a page
class PDFPageRenderer(Renderer):
    def get_elements(self, path: Path) -> List[PDFRendererElement]:
        elements = []
        doc = pymupdf.open(path)

        for page_number, page in enumerate(doc, start=1):
            e = PDFPageRendererElement(page_number, page)
            elements.append(e)

        return elements
