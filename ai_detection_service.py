"""
Heuristic signals for AI-like prose (not a trained classifier).
Combines sentence-length uniformity, vocabulary diversity, and repetition.
"""

from __future__ import annotations

import math
import re
from collections import Counter


_WORD = re.compile(r"\b\w+\b", re.UNICODE)
_SENT_SPLIT = re.compile(r"[.!?]+")


def _words(text: str) -> list[str]:
    return [m.group(0).lower() for m in _WORD.finditer(text or "")]


def _sentence_word_counts(text: str) -> list[int]:
    parts = [p.strip() for p in _SENT_SPLIT.split(text or "") if p.strip()]
    if not parts and (text or "").strip():
        parts = [(text or "").strip()]
    return [len(_words(s)) for s in parts if s]


def _score_sentence_length_variation(lengths: list[int]) -> float:
    """Higher return = more AI-like (uniform sentence lengths)."""
    if len(lengths) < 2:
        return 45.0
    mean = sum(lengths) / len(lengths)
    if mean < 1e-6:
        return 50.0
    variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    stdev = math.sqrt(variance)
    cv = stdev / mean
    # Very regular lengths (low CV) often read like templated / model output.
    if cv <= 0.18:
        return 88.0
    if cv >= 0.72:
        return 12.0
    return 88.0 - (cv - 0.18) / (0.72 - 0.18) * (88.0 - 12.0)


def _score_vocabulary_diversity(tokens: list[str]) -> float:
    """Higher return = more AI-like (low distinct-word ratio)."""
    n = len(tokens)
    if n == 0:
        return 0.0
    if n < 10:
        return 48.0
    distinct = len(set(tokens))
    ttr = distinct / n
    if ttr < 0.30:
        return min(100.0, 82.0 + (0.30 - ttr) * 120.0)
    if ttr > 0.58:
        return max(0.0, 22.0 - (ttr - 0.58) * 90.0)
    return 82.0 - (ttr - 0.30) / (0.58 - 0.30) * (82.0 - 22.0)


def _score_repetition(tokens: list[str]) -> float:
    """Higher return = more AI-like (repeated phrases / bigrams)."""
    if len(tokens) < 4:
        return 45.0
    bigrams = [tuple(tokens[i : i + 2]) for i in range(len(tokens) - 1)]
    total = len(bigrams)
    if total == 0:
        return 45.0
    counts = Counter(bigrams)
    dup_pressure = 1.0 - (len(counts) / total)
    top_share = counts.most_common(1)[0][1] / total
    raw = 0.62 * dup_pressure + 0.38 * min(1.0, top_share * 1.8)
    return min(100.0, raw * 100.0)


def compute_ai_probability(text: str) -> float:
    """
    Aggregate heuristic score: estimated probability text is AI-generated, 0–100.
    """
    stripped = (text or "").strip()
    if not stripped:
        return 0.0

    tokens = _words(stripped)
    lengths = _sentence_word_counts(stripped)

    s_len = _score_sentence_length_variation(lengths)
    s_vocab = _score_vocabulary_diversity(tokens)
    s_rep = _score_repetition(tokens)

    combined = (s_len + s_vocab + s_rep) / 3.0
    return round(max(0.0, min(100.0, combined)), 2)
