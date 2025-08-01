from dataclasses import dataclass
from typing import Callable, List
import re

@dataclass
class Span:
    start: int
    end: int
    text: str

    def overlaps_with(self, other: "Span") -> bool:
        return self.start <= other.end and other.start <= self.end

    def merge_with(self, other: "Span", words: List[str]) -> "Span":
        new_start = min(self.start, other.start)
        new_end = max(self.end, other.end)
        new_text = " ".join(words[new_start:new_end])
        return Span(start=new_start, end=new_end, text=new_text)

    def length(self) -> int:
        return self.end - self.start

def filter_overlapping(spans: List[Span], other: List[Span]) -> List[Span]:
    return [
        span for span in spans
        if any(span.overlaps_with(o) for o in other)
    ]

# underline text via ANSI escape codes
HIGHLIGHT_START = "\033[4m"
HIGHLIGHT_END = "\033[0m"

def highlight_ansi(word: str) -> str:
    return f"{HIGHLIGHT_START}{word}{HIGHLIGHT_END}"

def highlight_unicode(word: str) -> str:
    # underline text via unicode
    return "".join(c + "\u0332" for c in word)



def color_highlight_spans(text: str, spans: List[Span]) -> str:
    """
    Highlights multiple Span objects in a string using ANSI background colors.
    
    Args:
        text: The input string
        spans: A list of Span objects (with word-based start/end indices)
    """
    words = text.split()
    num_words = len(words)

    # Build word-level highlight flags
    highlight_flags = [False] * num_words
    for span in spans:
        if 0 <= span.start < span.end <= num_words:
            for i in range(span.start, span.end):
                highlight_flags[i] = True

    # Apply highlighting
    highlighted_words = [
        highlight_unicode(word) if flag else word
        for word, flag in zip(words, highlight_flags)
    ]

    return " ".join(highlighted_words)

# FIXME: duplicated in diffing.py
def extract_words(text):
    return re.findall(r'\b\w+\b', text)

def extract_and_merge_spans(
    text: str,
    min_window: int,
    max_window: int,
    checker: Callable[[List[Span]], List[Span]]
) -> List[Span]:
    #words = text.split()
    words = extract_words(text)
    all_spans: List[Span] = []

    for window_size in range(min_window, max_window + 1):
        for start in range(len(words) - window_size + 1):
            end = start + window_size
            text_segment = " ".join(words[start:end])
            all_spans.append(Span(start=start, end=end, text=text_segment))

    accepted_spans = checker(all_spans)
    if not accepted_spans:
        return []

    accepted_spans.sort(key=lambda s: s.start)
    merged: List[Span] = [accepted_spans[0]]

    for span in accepted_spans[1:]:
        last = merged[-1]
        if span.start <= last.end:
            merged[-1] = last.merge_with(span, words)
        else:
            merged.append(span)

    return merged

