from phantomlint.interfaces import OCREngine, Splitter, Analyzer, Differ, Renderer
from phantomlint.word_spans import Span, color_highlight_spans
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
    suspicious_phrases = [] # a list of pairs (full_phrase, spans)
    hidden_phrases = [] # a list of pairs (hidden,e), see below

    log.info("running analysis to detect suspicious phrases...")
    # do all the analysis before running further pipeline stages
    # to avoid intermixing analysis and OCR etc.
    for e in elements:
        full_text = normalize_text(e.get_text())
        full_text_phrases = list(splitter.split(full_text))
        flagged = analyzer.analyze(bad_phrases, full_text_phrases)
        if flagged:
            suspicious_phrases.append((flagged,e))

    with open(output_dir / SUSPICIOUS_PHRASES_FILE, "w", encoding="utf-8") as f:
        for (flagged,e) in suspicious_phrases:
            for str_span in flagged:
                (text,spans) = str_span
                f.write(f"\
Suspicious phrases found on page {e.page_number} inside the following text\n\
(additional suspicious text may also be present, but not highlighted):\n---\n")                
                f.write(color_highlight_spans(text,spans))
                f.write("\n---\n\n")

    log.info("detecting hidden suspicious phrases with OCR...")
    for (flagged,e) in suspicious_phrases:
        confirmed_hidden = []        
        for (f,spans) in flagged:
            img = e.render_image()
            ocr_text = normalize_text(ocr.extract_text([img]))
            ocr_phrases = list(splitter.split(ocr_text))
            hidden_spans = differ.find_hidden_spans(f, spans, ocr_phrases)            
            if hidden_spans:
                confirmed_hidden.append((hidden_spans,f))

        if confirmed_hidden:
            hidden_phrases.append((confirmed_hidden,e))
            
    with open(output_dir / HIDDEN_SUSPICIOUS_PHRASES_FILE, "w", encoding="utf-8") as f:
        for (hidden,e) in hidden_phrases:
            for (hidden_spans,text) in hidden:
                f.write(f"\
Hidden suspicious phrases found on page {e.page_number} inside the following text\n\
(additional hidden text may also be present, but not highlighted):\n---\n")
            f.write(color_highlight_spans(text,hidden_spans))
            f.write("\n---\n\n")
    
    verdict = "✅ Nothing detected."
    if len(hidden_phrases) > 0:
        verdict = f"❌ Hidden suspicious phrases detected. See {output_dir / HIDDEN_SUSPICIOUS_PHRASES_FILE}"

    print(verdict)
    log.info(verdict)
