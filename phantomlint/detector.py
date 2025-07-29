from phantomlint.interfaces import OCREngine, Splitter, Analyzer, Differ, Renderer
from pathlib import Path
from typing import List
import pymupdf  # PyMuPDF
import re
import unicodedata
import os
import logging

log = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    # remove ligatures and normalize whitespace
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text.strip())

SUSPICIOUS_PHRASES_FILE="suspicious_phrases.txt"
HIDDEN_SUSPICIOUS_PHRASES_FILE="hidden_suspicious_phrases.txt"

def detect_hidden_phrases(input_path: Path, output_dir: Path, ocr: OCREngine, splitter: Splitter, differ: Differ, analyzer: Analyzer, renderer: Renderer, bad_phrases: List[str]):
    output_dir.mkdir(parents=True, exist_ok=True)

    log = logging.getLogger(__name__)

    log.info("getting document elements...")
    elements = renderer.get_elements(input_path)
    suspicious_phrases = [] # a list of pairs (flagged,e), see below
    hidden_phrases = []

    log.info("running analysis to detect suspicious phrases...")
    # do all the analysis before running further pipeline stages
    # to avoid intermixing analysis and OCR etc.
    for e in elements:
        full_text = normalize_text(e.get_text())
        full_text_phrases = list(splitter.split(full_text))
        flagged = analyzer.analyze(bad_phrases, full_text_phrases)
        suspicious_phrases.append((flagged,e))

    with open(output_dir / SUSPICIOUS_PHRASES_FILE, "w", encoding="utf-8") as f:
        for (flagged,e) in suspicious_phrases:
            if flagged != []:
                f.write("\n".join(flagged))
                f.write("\n")        

    log.info("detecting hidden suspicious phrases with OCR...")
    for (flagged,e) in suspicious_phrases:
        for f in flagged:
            img = e.render_image()
            ocr_text = normalize_text(ocr.extract_text([img]))
            ocr_phrases = list(splitter.split(ocr_text))
            hidden = differ.find_hidden_phrases([f], ocr_phrases)
            hidden_phrases += hidden
            
    with open(output_dir / HIDDEN_SUSPICIOUS_PHRASES_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(hidden_phrases))
    
    verdict = "✅ Nothing detected."
    if len(hidden_phrases) > 0:
        verdict = f"❌ Hidden suspicious phrases detected. See {output_dir / HIDDEN_SUSPICIOUS_PHRASES_FILE}"

    print(verdict)
    log.info(verdict)
