from phantomlint.interfaces import Renderer, RendererElement
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from PIL import Image
from playwright.sync_api import sync_playwright
from io import BytesIO
import pymupdf  # PyMuPDF
import subprocess
import pikepdf
import tempfile
import re
import logging

log = logging.getLogger(__name__)

SUPPORTED_FILETYPES=["pdf","html","htm"]
def renderer_for(path: Path, dpi: int) -> Renderer:
    if path.suffix.lower() == ".pdf":
        return PDFRenderer(dpi)
    elif path.suffix.lower() in [".html", ".htm"]:
        log.warning("HTML support is currently experimental")
        return HTMLRenderer()
    else:
        return None


class HTMLRendererElement(RendererElement):
    def __init__(self, text: str, image: Image.Image, box):
        self.text = text
        self.image = image
        self.box = box
        self.page_number = 0 # FIXME: this shouldn't be relied on in detector.py

    def get_text(self) -> str:
        return self.text

    def render_image(self) -> Image.Image:
        # Crop and save image
        cropped = self.image.crop((
            int(self.box['x']),
            int(self.box['y']),
            int(self.box['x'] + self.box['width']),
            int(self.box['y'] + self.box['height'])
        ))

        return cropped

def get_text_node_handles(page):
    array_handle = page.evaluate_handle("""
    () => {
        const results = [];

        function walk(node) {
            // some HTML pages have very small text nodes, on which we won't detect anything
            if (node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 10) {
                results.push(node);
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                for (const child of node.childNodes) {
                    walk(child);
                }
            }
        }

        walk(document.body);
        return results;
    }
    """)
    props = array_handle.get_properties()
    # These are already JSHandle objects for text nodes
    return list(props.values())

def get_text_node_bounding_box(text_node_handle):
    return text_node_handle.evaluate("""
    (node) => {
        const range = document.createRange();
        range.selectNodeContents(node);
        const rect = range.getBoundingClientRect();
        return {
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height
        };
    }
    """)


class HTMLRenderer(Renderer):
    def get_elements(self, path: Path) -> List[HTMLRendererElement]:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            html_content = path.read_text(encoding="utf-8")
            page.set_content(html_content)
            screenshot_bytes = page.screenshot(full_page=True)
            image = Image.open(BytesIO(screenshot_bytes))

            res = get_text_node_handles(page)
            
            elements = []
            for node in res:
                text = node.evaluate("n => n.textContent.trim()")
                #log.info(f"Got text node '{text}'")
                box = get_text_node_bounding_box(node)
                if not box:
                    continue
                element = HTMLRendererElement(text, image, box)
                elements.append(element)
                
            return elements

# Notes on different PDF text rendering approaches:
# There are various challenges we might need to deal with:
# - Text that falls outside a page's CropBox
# - Text that falls outside a page's MediaBox
# - Text obscured by a (zero) Clipping Path
#
# At the same time, we ideally want a renderer approach that
# returns individual chunks of text with bounding boxes, i.e.
# is "localised"
#
# There are various text renderers we might use for PDF:
# - pymupdf
# - pdfminer.six
# - pdftotext
#
# Each has pros and cons, per the table below:
#
# Renderer      Sees outside   Sees outside    Ignores    Localised
# Approach       CropBox        MediaBox      Clipping    Rendering
# -------------------------------------------------------------------
#
#  pymupdf         no              no            no          yes
#
#  pdfminer.six    no              no            yes         yes
#     * NOTE: pdfminer.six sometimes misses text areas
#
#  pdftotext       yes             no            yes         no
#
# Therefore, we use the following strategy:
# 1. Use pymupdf to get images of each page, respecting CropBox etc.
# 2. Use pikepdf to remove CropBox and expand MediaBox on each page
# 3. Check for the presence of Clipping Paths, if present
# 4a.  Fall back to pdftotext -raw, foregoing localised rendering
# 4b.  Otherwise, use pymupdf but remember to account for MediaBox expansion
class PDFRendererElement(RendererElement):
    def __init__(self, page_number, page, block, image, zoom, expansion: int = 0):
        self.page = page
        self.page_number = page_number
        self.block = block
        self.image = image
        self.zoom = zoom
        self.expansion = expansion

    def get_text(self) -> str:
        block_text = ""
        for line in self.block.get("lines", []):
            for span in line.get("spans", []):
                block_text += span["text"]
                block_text += " "
            block_text += "\n"
        return block_text
        
    def render_image(self) -> Image.Image:
        # translate bbox coordinates to take into account the expansion that might have been applied
        bbx0, bby0, bbx1, bby1 = self.block["bbox"]
        bbox = (bbx0-self.expansion, bby0-self.expansion, bbx1-self.expansion, bby1-self.expansion)

        x0, y0, x1, y1 = [int(coord * self.zoom) for coord in bbox]

        # Clamp coordinates within image bounds
        image_width, image_height = self.image.size
        x0 = max(0, min(x0, image_width))
        x1 = max(0, min(x1, image_width))
        y0 = max(0, min(y0, image_height))
        y1 = max(0, min(y1, image_height))

        cropped_image = self.image.crop((x0, y0, x1, y1))
        return cropped_image
    
class PDFRenderer(Renderer):
    def __init__(self, dpi: int, expansion: int = 10000):
        self.dpi = dpi
        self.expansion = expansion
        
    def get_elements(self, path: Path) -> List[PDFRendererElement]:
        elements = []
        doc = pymupdf.open(path)
        num_pages = doc.page_count        

        # collect images of each page
        images = []    # is zero-indexed
        for page_number, page in enumerate(doc, start=1):
            zoom = self.dpi / 72.0  # PDF default resolution is 72 DPI
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(image)

        doc.close()

        # now remove CropBox and expand MediaBox of each page
        # and also make sure all OCGs are visible etc.
        with pikepdf.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_obj = page.obj
                if "/CropBox" in page_obj:
                    del page_obj["/CropBox"]
                if "/MediaBox" in page_obj:
                    media_box = list(page_obj["/MediaBox"])
                    media_box[0] = media_box[0] - self.expansion  # x0
                    media_box[1] = media_box[1] - self.expansion  # y0
                    media_box[2] = media_box[2] + self.expansion  # x1
                    media_box[3] = media_box[3] + self.expansion  # y1
                    page_obj["/MediaBox"] = pikepdf.Array(media_box)

            root = pdf.Root
            ocprops = root.get("/OCProperties", None)
            if isinstance(ocprops, pikepdf.Object):
                # Ensure default config dictionary exists
                d = ocprops.get("/D", None)
                if not isinstance(d, pikepdf.Dictionary):
                    d = pikepdf.Dictionary()
                    ocprops["/D"] = d

                # Make all groups visible by default
                d[pikepdf.Name("/BaseState")] = pikepdf.Name("/ON")

                # Remove explicit OFF/ON lists (not needed when BaseState=/ON)
                if "/OFF" in d:
                    del d["/OFF"]
                if "/ON" in d:
                    del d["/ON"]

                # Remove usage-based auto-states that some viewers apply
                if "/AS" in ocprops:
                    del ocprops["/AS"]

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf.save(tmp.name)
                log.info(f"pdf sans CropBox, with expanded MediaBox, saved {tmp.name}")

        # from now on, operate on the transformed pdf (sans CropBoxes etc.)
        path = tmp.name

        doc = pymupdf.open(path)
        for page_number, page in enumerate(doc, start=1):
            image = images[page_number-1]   # images is zero-indexed

            # check for clippping paths, since PyMuPDF won't return text
            # that is hidden by one of these.
            #
            # match rectangles followed by clip operators W or W* and n
            clipping_pattern = re.compile(
                rb"(\d+(\.\d+)?\s+){4}re\s+W\*?\s+n", re.MULTILINE
            )
            contents = page.read_contents()
            if contents and clipping_pattern.findall(contents):
                log.warning(f"Page {page_number} contains clipping paths. Using pdftotext renderer for it")
                e = PDFToTextPageRendererElement(page_number, path, image)
                elements.append(e)
                continue

            # if we don't find any lines on the page, fall back to using whole-page rendering
            found_lines=False
            for block in page.get_text("dict",clip=pymupdf.INFINITE_RECT())["blocks"]:
                if block["type"] != 0:  # Only text blocks
                    continue
                if block.get("lines", []) != []:
                    e = PDFRendererElement(page_number, page, block, image, zoom, self.expansion)
                    elements.append(e)
                    found_lines=True
            if not found_lines:
                log.info(f"No text lines found on page {page_number}. Using whole-page renderer for that page")
                e = PDFPageRendererElement(page_number, page, image)
                elements.append(e)
                
        return elements


class PDFPageRendererElement(RendererElement):
    def __init__(self, page_number, page, image):
        self.page = page
        self.page_number = page_number
        self.image = image
        
    def get_text(self) -> str:
        return self.page.get_text("text")

    def render_image(self) -> Image.Image:
        return self.image


class PDFToTextPageRendererElement(RendererElement):
    def __init__(self, page_number, path, image):
        self.path = path
        self.page_number = page_number
        self.image = image

        result = subprocess.run(
            ["pdftotext", "-raw", str(path), "-f", str(page_number), "-l", str(page_number), "-"],
            stdout=subprocess.PIPE,
            check=True
        )
        self.page_text = result.stdout.decode("utf-8")

    def get_text(self) -> str:
        return self.page_text

    def render_image(self) -> Image.Image:
        return self.image

