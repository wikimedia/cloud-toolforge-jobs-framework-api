import pytest

from tjf.job import validate_jobname, _remove_filelog_suffix


@pytest.mark.parametrize(
    "name, expected",
    [
        ["some-command 1>>example.out 2>>example.err", "some-command"],
        ["some-command 1>/dev/null 2>/dev/null", "some-command"],
    ],
)
def test_remove_filelog_suffix(name, expected):
    assert _remove_filelog_suffix(name) == expected


@pytest.mark.parametrize(
    "name",
    [
        "nöt-älphänümeriç!",
        "underscores_are_not_valid_in_dns",
        "nor..are..double..dots",
        ".or-starting-with-dots",
    ],
)
def test_invalid_jobname(name):
    with pytest.raises(Exception):
        validate_jobname(name)


@pytest.mark.parametrize(
    "name",
    [
        "totally-valid",
        "so.is.this",
    ],
)
def test_valid_jobname(name):
    assert validate_jobname(name) is None
