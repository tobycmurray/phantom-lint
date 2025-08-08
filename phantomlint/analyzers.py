from phantomlint.interfaces import Analyzer
from phantomlint.word_spans import extract_and_merge_spans, Span
from typing import List, Tuple
from sentence_transformers import SentenceTransformer, util
from llm_guard import scan_prompt
from llm_guard.input_scanners import PromptInjection

import re
import logging

log = logging.getLogger(__name__)

class PassthroughAnalyzer(Analyzer):
    def analyze(self, bad_phrases: List[str], phrases: List[str]) -> List[Tuple[str, List[Span]]]:
        ans = []
        for phrase in phrases:
            ans.append((phrase,[Span(start=0,end=len(phrase),text=phrase)]))
        return ans

def filter_text(text):
    return ''.join(c for c in text if c.isalpha() or c.isspace())

class LocalSemanticAnalyzer(Analyzer):
    def __init__(self, threshold: float = 0.75):
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.threshold = threshold

    def analyze(self, bad_phrases: List[str], phrases: List[str]) -> List[Tuple[str, List[Span]]]:
        known_embeddings = self.encoder.encode(bad_phrases, convert_to_tensor=True)

        # when analysing each phrase, break it up into sub-phrases
        # using a sliding window -- this helps to detect compound
        # instructions that otherwise go undetected, and also to
        # find instructions embedded inside text blocks that also
        # contain legitimite, visible text
        #
        # We set the minimum and maximum window sizes to be the
        # min and max of the word counts of the bad phrases
        window_sizes = [len(p.split()) for p in bad_phrases]
        min_window_size = min(window_sizes)
        max_window_size = max(window_sizes)        

        def checker(spans: List[Span]) -> List[Span]:
            if not spans:
                return []

            texts = [filter_text(span.text) for span in spans]
            span_embeddings = self.encoder.encode(texts, convert_to_tensor=True)

            # Compute cosine similarities
            similarity_matrix = util.cos_sim(span_embeddings, known_embeddings)  # [num_spans, num_known_phrases]

            # Determine which spans match at least one known phrase
            matches = []
            for i, span in enumerate(spans):
                max_score = similarity_matrix[i].max().item()
                if max_score >= self.threshold:
                    max_idx = similarity_matrix[i].argmax().item()
                    matches.append(span)
                    log.info(f"got match: \"{texts[i]}\" matches \"{bad_phrases[max_idx]}\" with score {max_score}")

            return matches

        matches = []
        for phrase in phrases:
            matched = extract_and_merge_spans(phrase, min_window_size, max_window_size, checker)
            if matched:
                matches.append((phrase,matched))
            
        return matches


class LLMGuardAnalyzer(Analyzer):
    def __init__(self):
        self.input_scanners = [PromptInjection(match_type="full")]

    def analyze(self, bad_phrases: List[str], phrases: List[str]) -> List[Tuple[str, List[Span]]]:
        matches = []
        for phrase in phrases:
            span=Span(start=0,end=len(phrase),text=phrase)
            sanitized_prompt, results_valid, results_score = scan_prompt(self.input_scanners, phrase)
            if any(not result for result in results_valid.values()):
                matches.append((phrase,[span]))                

        return matches
