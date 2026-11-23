"""Pure scoring helpers (no framework imports, so they are trivial to unit-test)."""

import math
import re

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")


def round_band(value: float) -> float:
    """Clamp to 0-9 and round to the nearest half band the way IELTS averages are rounded.

    Averages ending in .25 round up to .5 and .75 round up to the next whole band,
    i.e. values in [x.25, x.75) become x.5.
    """
    clamped = min(9.0, max(0.0, float(value)))
    return math.floor(clamped * 2 + 0.5) / 2


def overall_band(fluency: float, lexical: float, grammar: float) -> float:
    """Provisional overall band from the three criteria that can be judged from text.

    Pronunciation is the fourth official criterion and is not assessed (no audio yet).
    """
    return round_band((fluency + lexical + grammar) / 3)


def count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))
