import pytest
from tjf.cron import CronExpression, CronParsingError

SEED = "asdf"


def test_cron_parse_simple():
    assert CronExpression.parse("1 2 3 4 5", SEED).format() == "1 2 3 4 5"


def test_cron_parse_wildcards():
    assert CronExpression.parse("*/30 1,2 4-6 * *", SEED).format() == "*/30 1,2 4-6 * *"


def test_cron_parse_at_macro():
    expression = CronExpression.parse("@daily", SEED)
    assert expression.text == "@daily"
    # this changes based on the random seed
    assert expression.format() == "1 5 * * *"


def test_cron_parse_invalid_fields():
    with pytest.raises(
        CronParsingError, match="Expected to find 5 space-separated values, found 4"
    ):
        assert CronExpression.parse("1 2 3 4", SEED) is None


def test_cron_parse_nonsense_values():
    with pytest.raises(CronParsingError, match="Unable to parse"):
        assert CronExpression.parse("foo 2 3 4 5", SEED) is None

    with pytest.raises(CronParsingError, match="Invalid value"):
        assert CronExpression.parse("1000000 2 3 4 5", SEED) is None


def test_cron_parse_dash_slash():
    with pytest.raises(CronParsingError, match="Step syntax is not supported with ranges"):
        assert CronExpression.parse("1-2/3 2 3 4 5", SEED) is None


def test_cron_parse_invalid_range():
    with pytest.raises(
        CronParsingError, match="End value 0 must be smaller than start value 1000"
    ):
        assert CronExpression.parse("1000-0 2 3 4 5", SEED) is None

    with pytest.raises(CronParsingError, match="End value 2000 must be at most 59"):
        assert CronExpression.parse("1-2000 2 3 4 5", SEED) is None


def test_cron_parse_invalid_at_macro():
    with pytest.raises(CronParsingError, match="Invalid at-macro"):
        assert CronExpression.parse("@bananas", SEED) is None
