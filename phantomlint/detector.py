from phantomlint.interfaces import OCREngine, Splitter, Analyzer, Differ, Renderer
from pathlib import Path
from typing import List
import pymupdf  # PyMuPDF
import re
import unicodedata
import os

def normalize_text(text: str) -> str:
    # Remove ligatures and normalize whitespace
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text.strip())

def extract_pdf_text(pdf_path: Path) -> str:
    with pymupdf.open(pdf_path) as doc:
        return "\n".join(page.get_text() for page in doc)

FULL_TEXT_FILE="full_text.txt"
OCR_TEXT_FILE="ocr_text.txt"
TEXT_DIFF_FILE="text_diff.txt"
ANALYSIS_RESULTS_FILE="analysis_results.txt"

def detect_hidden_phrases(input_path: Path, output_dir: Path, ocr: OCREngine, splitter: Splitter, differ: Differ, analyzer: Analyzer, renderer: Renderer, dpi: int, threshold: float, bad_phrases: List[str]):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract full text
    print("extracting full text from input file...")
    full_text = normalize_text(renderer.extract_text(input_path))
    with open(output_dir / FULL_TEXT_FILE, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"full text saved in {output_dir / FULL_TEXT_FILE}")
    
    # Extract OCR text
    print("rendering images from input file...")
    images = renderer.render_images(input_path, dpi)
    print("OCR extracting text from images...")
    ocr_text = normalize_text(ocr.extract_text(images))
    with open(output_dir / OCR_TEXT_FILE, "w", encoding="utf-8") as f:
        f.write(ocr_text)
    print(f"OCR extracted text saved in {output_dir / OCR_TEXT_FILE}")
    
    # Identify phrases present in full text but not OCR
    print("splitting full text...")
    full_phrases = list(splitter.split(full_text))
    print("splitting OCR text...")
    ocr_phrases = list(splitter.split(ocr_text))
    print("identifying hidden phrases...")
    hidden_phrases = differ.find_hidden_phrases(full_phrases, ocr_phrases)
    with open(output_dir / TEXT_DIFF_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(hidden_phrases))
    print(f"hidden phrases saved in {output_dir / TEXT_DIFF_FILE}")

    # Analyze hidden phrases
    print("analyzing hidden phrases...")
    flagged = analyzer.analyze(bad_phrases, hidden_phrases)
    with open(output_dir / ANALYSIS_RESULTS_FILE, "w", encoding="utf-8") as f:
        for phrase in flagged:
            f.write(f"{phrase}\n")
    print(f"analysis results saved in {output_dir / ANALYSIS_RESULTS_FILE}")
    
    # Final verdict
    verdict = "✅ Nothing detected."
    if flagged:
        verdict = f"❌ Suspicious phrases detected. See {output_dir / ANALYSIS_RESULTS_FILE}"

    print(verdict)
