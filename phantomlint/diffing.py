from phantomlint.interfaces import Differ
from abc import ABC, abstractmethod
from typing import List
from sentence_transformers import SentenceTransformer, util
import logging
import re

log = logging.getLogger(__name__)

class ExactDiffer(Differ):
    def find_hidden_phrases(self, full_phrases: List[str], ocr_phrases: List[str]) -> List[str]:
        hidden = []
        for phrase in full_phrases:
            if phrase not in ocr_phrases:
                hidden.append(phrase)
        return hidden

class SemanticDiffer(Differ):
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def find_hidden_phrases(self, full_phrases: List[str], ocr_phrases: List[str]) -> List[str]:
        if len(ocr_phrases) == 0:
            return full_phrases

        ocr_embeddings = self.model.encode(ocr_phrases, convert_to_tensor=True)

        hidden = []
        for phrase in full_phrases:
            phrase_embedding = self.model.encode(phrase, convert_to_tensor=True)
            similarities = util.pytorch_cos_sim(phrase_embedding, ocr_embeddings)
            max_score = similarities.max().item()
            if max_score < self.threshold:
                hidden.append(phrase)
        return hidden

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

    def find_hidden_phrases(self, full_phrases: List[str], ocr_phrases: List[str]) -> List[str]:
        if len(ocr_phrases) == 0:
            return full_phrases

        hidden = []
        for phrase in full_phrases:
            phrase_words = self.extract_words(phrase)
            scores=[]
            for ocr in ocr_phrases:
                ocr_words = self.extract_words(ocr)
                prop = self.proportion_in_common(phrase_words, ocr_words)
                scores.append(prop)
            max_score = max(scores)
            if max_score < self.threshold:
                hidden.append(phrase)
        return hidden
