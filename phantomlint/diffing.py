from phantomlint.interfaces import Differ
from phantomlint.word_spans import Span, extract_and_merge_spans, filter_overlapping
from abc import ABC, abstractmethod
from typing import List
from sentence_transformers import SentenceTransformer, util
import logging
import re

log = logging.getLogger(__name__)

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "is", "are",
    "was", "were", "in", "on", "at", "of", "for", "to", "with", "as",
    "by", "from", "that", "this", "it", "be", "been", "being"
}

def filter_stopwords(words: List[str]) -> List[str]:
    return [w for w in words if w.lower() not in STOPWORDS]

APOSTROPHES = ["'", "’", "‘", "`", "´"]

class WordDiffer(Differ):
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold

    # extract all words from some text
    def extract_words(self, text):
        # Extract words including contractions
        words = re.findall(r"\b\w+(?:['’‘`´]\w+)*\b", text)
        # Remove all apostrophe variants from words
        cleaned = [re.sub(r"['’‘`´]", "", word) for word in words]
        return cleaned

    # compute the proportion of words in list1 that are present in list2
    def proportion_in_common(self, list1, list2):
        set2 = set(list2)  # Convert to set for fast lookup
        common = sum(1 for word in list1 if word in set2)
        return common / len(list1) if list1 else 0

    def find_hidden_spans(self, full_phrase: str, spans: List[Span], ocr_phrases: List[str]) -> List[Span]:
        if len(ocr_phrases) == 0:
            return Span(start=0,end=len(full_phrase),text=full_phrase)

        # TODO: is 3 a reasonable minimum?
        window_min=3
        window_max=len(full_phrase.split())
        orig_spans=spans # prevent shadowing in checker

        def checker(spans: List[Span]) -> List[Span]:
            if not spans:
                return []

            spans=filter_overlapping(spans, orig_spans)

            texts = [span.text for span in spans]

            hidden = []
            for i,span in enumerate(spans):
                text=texts[i]
                span_words = filter_stopwords(self.extract_words(text))

                # ignore spans that contain only stopwords
                if not span_words:
                    continue

                scores=[]
                for ocr in ocr_phrases:
                    ocr_words = filter_stopwords(self.extract_words(ocr))
                    prop = self.proportion_in_common(span_words, ocr_words)
                    scores.append(prop)
                max_score = max(scores)
                if max_score <= 1.0-self.threshold:
                    hidden.append(span)
            return hidden

        hidden=extract_and_merge_spans(full_phrase, window_min, window_max, checker)
        return hidden
