import pytest
from tjf.utils import format_duration


@pytest.mark.parametrize(
    "seconds, expected",
    [
        (0, "0s"),
        (1, "1s"),
        (20, "20s"),
        (60, "1m"),
        (61, "1m1s"),
        (120, "2m"),
        (121, "2m1s"),
        (3600, "1h"),
        (3601, "1h1s"),
        (3660, "1h1m"),
        (3661, "1h1m1s"),
        # for durations longer than a day, seconds are no longer relevant
        (86400, "1d"),
        (86401, "1d"),
        (86460, "1d1m"),
        (90000, "1d1h"),
        (90060, "1d1h1m"),
        (90061, "1d1h1m"),
        (90120, "1d1h2m"),
        (172800, "2d"),
    ],
)
def test_format_duration(seconds: int, expected: str):
    assert format_duration(seconds) == expected
