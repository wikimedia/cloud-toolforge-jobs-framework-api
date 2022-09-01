import pytest

from tjf.job import validate_jobname


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


@pytest.mark.parametrize("name", ["totally-valid", "so.is.this"])
def test_valid_jobname(name):
    assert validate_jobname(name) is None
