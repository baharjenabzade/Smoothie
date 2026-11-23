import pytest

from app.core.scoring import count_words, overall_band, round_band


@pytest.mark.parametrize(
    "value, expected",
    [
        (6.0, 6.0),
        (6.1, 6.0),
        (6.25, 6.5),   # .25 rounds up to .5
        (6.33, 6.5),
        (6.5, 6.5),
        (6.74, 6.5),
        (6.75, 7.0),   # .75 rounds up to the next whole band
        (8.9, 9.0),
        (-1, 0.0),     # clamped
        (12, 9.0),     # clamped
    ],
)
def test_round_band(value, expected):
    assert round_band(value) == expected


@pytest.mark.parametrize(
    "scores, expected",
    [
        ((6.0, 6.0, 7.0), 6.5),
        ((5.5, 6.0, 6.0), 6.0),
        ((7.0, 7.0, 7.5), 7.0),
        ((6.0, 6.5, 6.5), 6.5),
    ],
)
def test_overall_band(scores, expected):
    assert overall_band(*scores) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", 0),
        ("I don't know", 3),
        ("It's 5 o'clock!", 3),
        ("a well-known city", 3),
        ("  lots   of   spaces  ", 3),
    ],
)
def test_count_words(text, expected):
    assert count_words(text) == expected
