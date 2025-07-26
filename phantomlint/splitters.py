from phantomlint.interfaces import Splitter
import re
import spacy
from typing import List

from spacy.cli import download

def get_nlp_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        print("Downloading spaCy model 'en_core_web_sm'...")
        download("en_core_web_sm")
        return spacy.load("en_core_web_sm")
nlp = get_nlp_model()

class RegexSplitter(Splitter):
    def split(self, text: str) -> List[str]:
        return re.split(r'(?<=[.!?])\s+', text)

class SpacySplitter(Splitter):
    def split(self, text: str) -> List[str]:
        doc = nlp(text)
        return [sent.text.strip() for sent in doc.sents]

class SlidingWindowSplitter(Splitter):
    def __init__(self, window_size: int = 15, step: int = 1):
        self.window_size = window_size
        self.step = step

    def split(self, text: str) -> List[str]:
        words = re.findall(r"\w+|[.,!?;]", text)
        windows = [
            " ".join(words[i:i + self.window_size])
            for i in range(0, len(words) - self.window_size + 1, self.step)
        ]
        return windows
    
class GroupedSplitter(Splitter):
    def __init__(self, max_group_size: int = 2, short_sent_threshold: int = 40):
        self.max_group_size = max_group_size
        self.short_sent_threshold = short_sent_threshold

    def split(self, text: str) -> List[str]:
        doc = nlp(text)
        sentences = list(doc.sents)
        groups = []
        i = 0
        while i < len(sentences):
            current = sentences[i]
            group = [current.text.strip()]
            while (i + 1 < len(sentences) and
                   len(sentences[i + 1].text.strip()) < self.short_sent_threshold and
                   len(group) < self.max_group_size):
                i += 1
                group.append(sentences[i].text.strip())
            groups.append(" ".join(group))
            i += 1
        return groups
