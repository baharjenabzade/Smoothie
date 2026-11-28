"""Group questions that ask about the same thing, with no AI call.

Questions are reduced to their content-word stems and compared with cosine similarity. Grouping is
"leader" clustering (each question joins the most similar existing group, judged against that
group's first question), which avoids the long chains that single-link grouping produces.
"""

import math
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

_WORD = re.compile(r"[a-z]{3,}")
# question words, auxiliaries and filler that say nothing about the topic
_STOP = frozenset(
    ["the", "and", "for", "are", "was", "were", "you", "your", "yours", "with", "that", "this", "these", "those", "they", "them", "their", "there", "what", "when", "where", "which", "who", "whom", "whose", "why", "how", "does", "did", "doing", "done", "have", "has", "had", "having", "can", "could", "would", "should", "will", "shall", "may", "might", "must", "not", "but", "about", "from", "into", "onto", "over", "under", "than", "then", "too", "very", "really", "just", "also", "ever", "any", "some", "more", "most", "much", "many", "one", "two", "each", "other", "another", "such", "only", "own", "same", "both", "either", "neither", "whether", "say", "tell", "describe", "explain", "mention", "please", "like", "likes", "often", "usually", "sometimes", "think", "thought", "feel", "feeling", "want", "wanted", "need", "get", "got", "make", "made", "take", "took", "give", "gave", "people", "person", "thing", "things", "good", "bad", "kind", "kinds", "way", "ways", "lot", "time", "times", "year", "years", "day", "days", "important", "different", "similar", "well", "still", "yet", "always", "never", "now", "today", "nowadays", "currently", "recently", "past", "future", "first", "last", "next"]
)


def stem(word: str) -> str:
    for suffix, minimum in (("ies", 5), ("ing", 6), ("ed", 5), ("es", 5), ("ly", 5), ("s", 4)):
        if word.endswith(suffix) and len(word) >= minimum:
            word = word[: -len(suffix)] + ("y" if suffix == "ies" else "")
            break
    return word


def keywords(text: str) -> dict[str, str]:
    """stem -> a readable surface word, for the content words of ``text``."""
    out: dict[str, str] = {}
    for word in _WORD.findall(text.lower()):
        if word not in _STOP:
            out.setdefault(stem(word), word)
    return out


def similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / math.sqrt(len(a) * len(b))


@dataclass
class Item:
    key: int
    text: str
    stems: frozenset[str]

    @classmethod
    def of(cls, key: int, text: str) -> "Item":
        return cls(key, text, frozenset(keywords(text)))


def group_similar(items: Sequence[Item], threshold: float = 0.4) -> list[list[Item]]:
    """Leader clustering. Items with no content words end up alone."""
    groups: list[list[Item]] = []
    for item in items:
        best, best_score = None, 0.0
        for group in groups:
            score = similarity(item.stems, group[0].stems)
            if score > best_score:
                best, best_score = group, score
        if best is not None and best_score >= threshold:
            best.append(item)
        else:
            groups.append([item])
    return groups


def label_for(texts: Sequence[str]) -> str:
    """A short readable name for a group: its most common content words."""
    counts: Counter[str] = Counter()
    surface: dict[str, str] = {}
    for text in texts:
        for st, word in keywords(text).items():
            counts[st] += 1
            surface.setdefault(st, word)
    ranked = counts.most_common(2)
    if not ranked:
        return "Mixed questions"
    top = [surface[ranked[0][0]]]
    if len(ranked) > 1 and ranked[1][1] >= 2 and ranked[1][1] * 2 >= len(texts):  # a second word only if most questions share it
        top.append(surface[ranked[1][0]])
    return " & ".join(w.capitalize() for w in top)


def most_similar(target: Item, pool: Sequence[Item], limit: int = 8, minimum: float = 0.3) -> list[tuple[Item, float]]:
    scored = [(item, similarity(target.stems, item.stems)) for item in pool if item.key != target.key]
    return sorted((s for s in scored if s[1] >= minimum), key=lambda s: (-s[1], s[0].key))[:limit]
