from phantomlint.interfaces import OCREngine
from pathlib import Path
import pytesseract
from typing import List
from PIL import Image
# imports for LayoutParserOCREngine, currently unused
#import layoutparser as lp
# imports for OCRMyPDFEngine, currently unused
#import ocrmypdf
#import pymupdf
#import tempfile
# imports for PaddleOCREngine, currently unused
#from paddleocr import PaddleOCR
#import numpy as np
#import cv2
#import time
import logging

log = logging.getLogger(__name__)

class TesseractOCREngine(OCREngine):
    def extract_text(self, images: List[Image.Image]) -> str:
        return "\n".join(pytesseract.image_to_string(img, config='--psm 1 --oem 1') for img in images)


# this seems to hang, unfortunately
# class PaddleOCREngine(OCREngine):
#     def __init__(self):
#         self.ocr = PaddleOCR(use_angle_cls=False, lang='en')  # Faster, angle detection disabled

#     def extract_text(self, images: List[Image.Image]) -> str:
#         all_text = []
#         total = len(images)

#         for i, image in enumerate(images, 1):
#             try:
#                 image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
#                 result = self.ocr.ocr(image_cv)
#                 if not result or not result[0]:
#                     continue

#                 for line in result[0]:
#                     text = line[1][0].strip()
#                     all_text.append(text)


#             except Exception as e:
#                 log.error(f"  OCR failed on page {i}: {e}")

#         return "\n".join(all_text)


# attempt to use a different OCR strategy, which doesn't really work
# this doesn't do any better than tesseract, and in any case it breaks the
# current abstractions and architecture defined by interfaces.py
# class OCRMyPDFEngine(OCREngine):
#     def extract_text(self, images: List[Image.Image]) -> str:
#         with tempfile.TemporaryDirectory() as tmpdir:
#             raster_pdf_path = Path(tmpdir) / "input.pdf"
#             ocr_pdf_path = Path(tmpdir) / "ocr_output.pdf"

#             # save images as raster-only PDF
#             images[0].save(raster_pdf_path, save_all=True, append_images=images[1:], format="PDF")

#             # add OCR layer to PDF
#             ocrmypdf.ocr(
#                 input_file=str(raster_pdf_path),
#                 output_file=str(ocr_pdf_path),
#                 language="eng",
#                 deskew=True,
#                 optimize=0 # disable all optimization passes, including jbig2
#             )

#             # extract text from OCR-enhanced PDF
#             with pymupdf.open(ocr_pdf_path) as doc:
#                 return "\n".join(page.get_text() for page in doc)
            
# attempt to use LayoutParser to get better OCR, but I couldn't get the former working
# class LayoutParserOCREngine(OCREngine): def __init__(self,
#     ocr_config="--psm 6",
#     model_name="lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config"):
#     self.emodel = lp.PaddleDetectionLayoutModel( #model_name
#     config_path=model_name, threshold=0.5, label_map={0: "Text"},
#     enforce_cpu=True # Set to False if GPU is available and configured
#     ) self.ocr_config = ocr_config

#     def extract_text(self, images: List[Image.Image]) -> str: all_text
#         = [] for image in images: layout = self.model.detect(image)
#         text_blocks = [b for b in layout if b.type == "Text"]
#         text_blocks.sort(key=lambda b: (b.block.y_1, b.block.x_1))

#             for block in text_blocks: segment = block.pad(left=20,
#                 right=20, top=20, bottom=20) cropped =
#                 segment.crop_image(image) text =
#                 pytesseract.image_to_string(cropped,
#                 config=self.ocr_config) all_text.append(text.strip())

#         return "\n".join(all_text)
