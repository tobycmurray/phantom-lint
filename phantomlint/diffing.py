from phantomlint.interfaces import Differ
from abc import ABC, abstractmethod
from typing import List
from sentence_transformers import SentenceTransformer, util

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
        ocr_embeddings = self.model.encode(ocr_phrases, convert_to_tensor=True)

        hidden = []
        for phrase in full_phrases:
            phrase_embedding = self.model.encode(phrase, convert_to_tensor=True)
            similarities = util.pytorch_cos_sim(phrase_embedding, ocr_embeddings)
            max_score = similarities.max().item()

            # Debug output
            # print(f"Phrase: {phrase}\n  Max similarity: {max_score:.3f}")

            if max_score < self.threshold:
                hidden.append(phrase)

        return hidden
