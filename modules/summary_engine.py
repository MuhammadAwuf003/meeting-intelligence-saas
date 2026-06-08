"""
Summary engine: generates a concise meeting summary using NLP techniques.
Uses sentence scoring based on TF-IDF-style term frequency and position weighting.
"""

import re
import math
import logging
from collections import Counter
from typing import Optional

logger = logging.getLogger(__name__)

# Common English stop words (lightweight, no external dependency)
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "through", "during",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "shall", "can", "need", "dare", "ought", "used", "it", "its", "this",
    "that", "these", "those", "i", "we", "you", "he", "she", "they", "what",
    "which", "who", "whom", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "not",
    "only", "same", "so", "than", "too", "very", "just", "as", "if",
}

BUSINESS_KEYWORDS = {
    "decision", "decided", "agreed", "approved", "action", "task", "deadline",
    "launch", "release", "deploy", "migrate", "update", "review", "meeting",
    "project", "team", "budget", "timeline", "priority", "milestone", "goal",
    "strategy", "plan", "objective", "outcome", "result", "issue", "risk",
    "blocker", "dependency", "stakeholder", "client", "customer", "product",
}


def _tokenize_sentences(text: str) -> list[str]:
    """Split text into sentences using punctuation heuristics."""
    # Split on . ! ? followed by whitespace and capital letter
    sentence_endings = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
    sentences = sentence_endings.split(text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def _tokenize_words(sentence: str) -> list[str]:
    """Lowercase, strip punctuation, remove stop words."""
    words = re.findall(r"\b[a-zA-Z]{2,}\b", sentence.lower())
    return [w for w in words if w not in STOP_WORDS]


def _score_sentences(sentences: list[str]) -> list[tuple[float, str]]:
    """
    Score each sentence based on:
    - Term frequency of content words
    - Business keyword presence (boosted weight)
    - Position (earlier sentences weighted higher)
    """
    # Build corpus term frequency
    all_words: list[str] = []
    sentence_words = [_tokenize_words(s) for s in sentences]
    for words in sentence_words:
        all_words.extend(words)

    total = len(all_words) or 1
    tf: Counter = Counter(all_words)

    scored: list[tuple[float, str]] = []
    n = len(sentences)

    for idx, (sentence, words) in enumerate(zip(sentences, sentence_words)):
        if not words:
            scored.append((0.0, sentence))
            continue

        # TF score: average TF of words in sentence
        tf_score = sum(tf[w] / total for w in words) / len(words)

        # Business keyword boost
        biz_boost = sum(1.0 for w in words if w in BUSINESS_KEYWORDS) * 0.05

        # Position weight: first 20 % of sentences get a bonus
        position_weight = 1.3 if idx < max(1, n * 0.2) else 1.0

        final_score = (tf_score + biz_boost) * position_weight
        scored.append((final_score, sentence))

    return scored


def generate_summary(transcript: str, num_sentences: int = 6) -> str:
    """
    Generate a concise extractive summary of the transcript.

    Args:
        transcript: cleaned meeting transcript
        num_sentences: target number of summary sentences

    Returns:
        Formatted summary string
    """
    if not transcript or not transcript.strip():
        return "No transcript content available to summarize."

    sentences = _tokenize_sentences(transcript)

    if len(sentences) <= num_sentences:
        # Short transcript: return as-is
        return " ".join(sentences)

    scored = _score_sentences(sentences)

    # Select top-N sentences, preserve original order
    top_indices = sorted(
        range(len(scored)),
        key=lambda i: scored[i][0],
        reverse=True,
    )[:num_sentences]

    top_indices_sorted = sorted(top_indices)
    summary_sentences = [sentences[i] for i in top_indices_sorted]

    return " ".join(summary_sentences)


def extract_key_topics(transcript: str, top_n: int = 8) -> list[str]:
    """
    Extract the most prominent topics/keywords from the transcript.

    Returns a list of up to top_n keyword strings.
    """
    words = _tokenize_words(transcript)
    freq = Counter(words)

    # Boost business keywords
    boosted: dict[str, float] = {}
    for word, count in freq.items():
        boost = 2.0 if word in BUSINESS_KEYWORDS else 1.0
        boosted[word] = count * boost

    sorted_words = sorted(boosted.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]
