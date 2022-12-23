import pytest

from tjf.command import _remove_filelog_suffix


@pytest.mark.parametrize(
    "name, expected",
    [
        ["some-command 1>>example.out 2>>example.err", "some-command"],
        ["some-command 1>/dev/null 2>/dev/null", "some-command"],
    ],
)
def test_remove_filelog_suffix(name, expected):
    assert _remove_filelog_suffix(name) == expected
