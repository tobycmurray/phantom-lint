from phantomlint.interfaces import Analyzer
from phantomlint.word_spans import extract_and_merge_spans, Span
from typing import List, Tuple
from sentence_transformers import SentenceTransformer, util
#from llm_guard.input_scanners import PromptInjection
#from llm_guard.validators import InputValidator
import logging

log = logging.getLogger(__name__)

class PassthroughAnalyzer(Analyzer):
    def analyze(self, bad_phrases: List[str], phrases: List[str]) -> List[Tuple[str, List[Span]]]:
        ans = []
        for phrase in phrases:
            ans.append((phrase,[Span(start=0,end=len(phrase),text=phrase)]))
        return ans

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

            texts = [span.text for span in spans]
            span_embeddings = self.encoder.encode(texts, convert_to_tensor=True)

            # Compute cosine similarities
            similarity_matrix = util.cos_sim(span_embeddings, known_embeddings)  # [num_spans, num_known_phrases]

            # Determine which spans match at least one known phrase
            matches = []
            for i, span in enumerate(spans):
                max_score = similarity_matrix[i].max().item()
                if max_score >= self.threshold:
                    matches.append(span)

            return matches

        matches = []
        for phrase in phrases:
            matched = extract_and_merge_spans(phrase, min_window_size, max_window_size, checker)
            if matched:
                matches.append((phrase,matched))
            
        return matches


# I currently cannot get llm-guard working on my machine
# class LLMGuardAnalyzer(Analyzer):
#     def __init__(self, threshold: float = 0.5):
#         self.validator = InputValidator(scanners=[PromptInjection(min_score=threshold)])
#         self.threshold = threshold

#     def analyze(self, phrases: List[str]) -> List[str]:
#         flagged = []
#         for phrase in phrases:
#             result, _ = self.validator.validate(phrase)
#             if not result["is_valid"]:
#                 flagged.append(phrase)
#         return flagged
