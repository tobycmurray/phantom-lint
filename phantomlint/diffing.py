from phantomlint.interfaces import Differ
from phantomlint.word_spans import Span, extract_and_merge_spans, filter_overlapping
from phantomlint.nlp import nlp
from abc import ABC, abstractmethod
from typing import List
from sentence_transformers import SentenceTransformer, util
import logging
import re

log = logging.getLogger(__name__)

class ExactDiffer(Differ):
    def find_hidden_spans(self, full_phrase: List[str], ocr_phrases: List[str]) -> List[Span]:
        if full_phrase not in ocr_phrases:
            return []
        return Span(start=0,end=len(full_phrase),text=full_phrase)

class SemanticDiffer(Differ):
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def find_hidden_spans(self, full_phrase: str, ocr_phrases: List[str]) -> List[Span]:
        log.error("SemanticDiffer.find_hidden_spans not implemented (yet). Returning nothing")
        return []
        # if len(ocr_phrases) == 0:
        #     return full_phrases
        # ocr_embeddings = self.model.encode(ocr_phrases, convert_to_tensor=True)
        # hidden = []
        # for phrase in full_phrases:
        #     phrase_embedding = self.model.encode(phrase, convert_to_tensor=True)
        #     similarities = util.pytorch_cos_sim(phrase_embedding, ocr_embeddings)
        #     max_score = similarities.max().item()
        #     if max_score < self.threshold:
        #         hidden.append(phrase)
        # return hidden

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "is", "are",
    "was", "were", "in", "on", "at", "of", "for", "to", "with", "as",
    "by", "from", "that", "this", "it", "be", "been", "being"
}

def filter_stopwords(words: List[str]) -> List[str]:
    return [w for w in words if w.lower() not in STOPWORDS]

class WordDiffer(Differ):
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold

    # extract all words from some text
    def extract_words(self, text):
        return re.findall(r'\b\w+\b', text)

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
                span_words = self.extract_words(text)
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
