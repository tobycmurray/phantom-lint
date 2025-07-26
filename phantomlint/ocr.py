from phantomlint.interfaces import OCREngine
from pathlib import Path
import pytesseract
from typing import List
from PIL import Image

class TesseractOCREngine(OCREngine):
    def extract_text(self, images: List[Image.Image]) -> str:
        return "\n".join(pytesseract.image_to_string(img, config='--psm 1') for img in images)
