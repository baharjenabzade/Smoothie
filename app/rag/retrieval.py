"""Dependency-free retrieval (BM25) over the reference samples.

The point of retrieval here is calibration: show the model a few graded answers to the same part,
about similar topics, at *different* bands, so it learns how strict the platform owner is.
"""

import logging
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from app.rag.samples import ReferenceSample, load_samples

_TOKEN = re.compile(r"[a-z0-9']+")
_STOP = frozenset(
    ["a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "at", "for", "with", "is", "are", "was", "were", "be", "been", "it", "its", "this", "that", "these", "those", "i", "you", "he", "she", "we", "they", "my", "your", "his", "her", "our", "their", "me", "do", "does", "did", "have", "has", "had", "not", "so", "as", "by", "from", "about", "what", "which", "who", "how", "why", "when", "where", "can", "could", "would", "should", "will", "just", "very", "really"]
)
K1, B = 1.5, 0.75
logger = logging.getLogger(__name__)


def tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower().replace("’", "'")) if t not in _STOP and len(t) > 1]


class SampleIndex:
    def __init__(self, samples: list[ReferenceSample]) -> None:
        self.samples = samples
        # The question and topic count double: matching topics matters more than matching filler words.
        self._docs = [
            Counter(tokens(f"{s.question} {s.question} {s.topic or ''} {s.topic or ''} {s.answer}"))
            for s in samples
        ]
        self._len = [sum(d.values()) for d in self._docs]
        self._avg = (sum(self._len) / len(self._len)) if self._len else 1.0
        df: Counter[str] = Counter()
        for d in self._docs:
            df.update(d.keys())
        n = len(self._docs)
        self._idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def __len__(self) -> int:
        return len(self.samples)

    def _score(self, i: int, query: list[str]) -> float:
        doc, dl = self._docs[i], self._len[i]
        total = 0.0
        for term in set(query):
            tf = doc.get(term, 0)
            if tf:
                total += self._idf[term] * tf * (K1 + 1) / (tf + K1 * (1 - B + B * dl / self._avg))
        return total

    def select(self, *, part: int, question: str, answer: str, k: int = 3) -> list[ReferenceSample]:
        """Up to k samples of this part: most relevant first, preferring a spread of bands."""
        query = tokens(f"{question} {answer}")
        ranked = sorted(
            (i for i, s in enumerate(self.samples) if s.part == part),
            key=lambda i: (-self._score(i, query), -self.samples[i].band),
        )
        chosen: list[int] = []
        seen_bands: set[float] = set()
        for i in ranked:  # first pass: one per band
            if len(chosen) >= k:
                break
            if self.samples[i].band not in seen_bands:
                chosen.append(i)
                seen_bands.add(self.samples[i].band)
        for i in ranked:  # second pass: fill remaining slots by relevance
            if len(chosen) >= k:
                break
            if i not in chosen:
                chosen.append(i)
        return [self.samples[i] for i in sorted(chosen, key=lambda i: self.samples[i].band)]


def samples_dir() -> Path:
    from app.core.config import (
        get_settings,  # lazy: keeps the pure retrieval code importable alone
    )

    path = Path(get_settings().rag_samples_dir)
    return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path


@lru_cache
def get_index() -> SampleIndex:
    samples, problems = load_samples(samples_dir())
    for problem in problems:
        logger.warning("RAG samples: %s", problem)
    return SampleIndex(samples)


def reference_samples_for(*, part: int, question: str, answer: str) -> list[ReferenceSample]:
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.rag_enabled or settings.rag_top_k <= 0:
        return []
    return get_index().select(part=part, question=question, answer=answer, k=settings.rag_top_k)
