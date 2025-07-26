from phantomlint.interfaces import OCREngine, Splitter, Analyzer, Differ, Renderer
from pathlib import Path
import fitz  # PyMuPDF
import re
import unicodedata
import os

def normalize_text(text: str) -> str:
    # Remove ligatures and normalize whitespace
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text.strip())

def extract_pdf_text(pdf_path: Path) -> str:
    with fitz.open(pdf_path) as doc:
        return "\n".join(page.get_text() for page in doc)

FULL_TEXT_FILE="full_text.txt"
OCR_TEXT_FILE="ocr_text.txt"
TEXT_DIFF_FILE="text_diff.txt"
ANALYSIS_RESULTS_FILE="analysis_results.txt"

def detect_hidden_phrases(input_path: Path, output_dir: Path, ocr: OCREngine, splitter: Splitter, differ: Differ, analyzer: Analyzer, renderer: Renderer, dpi: int, threshold: float):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract full text
    full_text = normalize_text(renderer.extract_text(input_path))
    with open(output_dir / FULL_TEXT_FILE, "w", encoding="utf-8") as f:
        f.write(full_text)

    # Extract OCR text
    images = renderer.render_images(input_path, dpi)
    ocr_text = normalize_text(ocr.extract_text(images))
    with open(output_dir / OCR_TEXT_FILE, "w", encoding="utf-8") as f:
        f.write(ocr_text)

    # Identify phrases present in full text but not OCR
    full_phrases = list(splitter.split(full_text))
    ocr_phrases = list(splitter.split(ocr_text))
    hidden_phrases = differ.find_hidden_phrases(full_phrases, ocr_phrases)
    with open(output_dir / TEXT_DIFF_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(hidden_phrases))

    # Analyze hidden phrases
    flagged = analyzer.analyze(hidden_phrases)
    with open(output_dir / ANALYSIS_RESULTS_FILE, "w", encoding="utf-8") as f:
        for phrase in flagged:
            f.write(f"{phrase}\n")

    # Final verdict
    verdict = "✅ Nothing detected."
    if flagged:
        verdict = f"❌ Suspicious phrases detected. See {output_dir / ANALYSIS_RESULTS_FILE}"

    print(verdict)
