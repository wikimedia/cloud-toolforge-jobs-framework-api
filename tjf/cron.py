from dataclasses import dataclass
import random
from typing import Dict, List, Optional
from tjf.error import TjfValidationError


class CronParsingError(TjfValidationError):
    """Raised when a cron input fails to parse."""

    pass


@dataclass
class CronField:
    min: int
    max: int
    mapping: Optional[Dict[str, str]] = None


AT_MAPPING: Dict[str, str] = {
    "@hourly": "0 * * * *",
    "@daily": "0 0 * * *",
    "@weekly": "0 0 * * 0",
    "@monthly": "0 0 1 * *",
    "@yearly": "0 0 1 1 *",
}

FIELDS: List[CronField] = [
    CronField(min=0, max=59),
    CronField(min=0, max=23),
    CronField(min=1, max=31),
    CronField(min=1, max=12),
    CronField(
        min=0,
        max=6,
        mapping={
            # map 7 to 0 for both to match Sunday
            "7": "0",
            "sun": "0",
            "mon": "1",
            "tue": "2",
            "wed": "3",
            "thu": "4",
            "fri": "5",
            "sat": "6",
        },
    ),
]


def _assert_value(value: str, field: CronField) -> None:
    for entry in value.split(","):
        if "-" in entry:
            # step is not supported with 'a-b' syntax
            step = None

            if "/" in entry:
                raise CronParsingError("Step syntax is not supported with ranges")
        elif "/" in entry:
            entry, step = entry.split("/", 1)
        else:
            step = None

        if "-" in entry:
            start, end = entry.split("-", 1)

            try:
                start_int = int(start)
            except ValueError:
                raise CronParsingError(f"Unable to parse '{start}' as an integer")

            try:
                end_int = int(end)
            except ValueError:
                raise CronParsingError(f"Unable to parse '{end}' as an integer")

            if start_int > end_int:
                raise CronParsingError(
                    f"End value {end_int} must be smaller than start value {start_int}"
                )
            if start_int < field.min:
                raise CronParsingError(f"Start value {start_int} must be at least {field.min}")
            if end_int > field.max:
                raise CronParsingError(f"End value {end_int} must be at most {field.max}")

        elif entry != "*":
            if field.mapping and entry in field.mapping:
                entry = field.mapping[entry]

            try:
                field_int = int(entry)
            except ValueError:
                raise CronParsingError(f"Unable to parse '{entry}' as an integer")

            if field_int < field.min or field_int > field.max:
                raise CronParsingError(
                    f"Invalid value '{entry}', expected {field.min}-{field.max}"
                )

        if step:
            try:
                step_int = int(step)
            except ValueError:
                raise CronParsingError(f"Unable to parse '{step}' (from '{entry}') as an integer")

            if step_int == 0 or step_int < field.min or step_int > field.max:
                raise CronParsingError(f"Invalid step value in '{entry}'")


class CronExpression:
    def __init__(
        self, text: str, minute: str, hour: str, day: str, month: str, day_of_week: str
    ) -> None:
        self.text = text

        self.minute = minute
        self.hour = hour
        self.day = day
        self.month = month
        self.day_of_week = day_of_week

    def format(self) -> str:
        return f"{self.minute} {self.hour} {self.day} {self.month} {self.day_of_week}"

    @classmethod
    def parse(cls, value: str, random_seed: str) -> "CronExpression":
        if value.startswith("@"):
            mapped = AT_MAPPING.get(value, None)
            if not mapped:
                raise CronParsingError(
                    f"Invalid at-macro '{value}', supported macros are: {', '.join(AT_MAPPING.keys())}"
                )
            parts = mapped.split(" ")

            # provide consistent times for the same job
            random.seed(random_seed)

            for i, field in enumerate(FIELDS):
                if parts[i] == "*":
                    continue
                parts[i] = str(random.randint(field.min, field.max))

            # reset randomness to a non-deterministic seed
            random.seed()

        else:
            parts = [part for part in value.lower().split(" ") if part != ""]
            if len(parts) != 5:
                raise CronParsingError(
                    f"Expected to find 5 space-separated values, found {len(parts)}"
                )

            for i, field in enumerate(FIELDS):
                _assert_value(parts[i], field)

        return cls(
            value,
            *parts,
        )

    @classmethod
    def from_job(cls, actual: str, configured: str) -> "CronExpression":
        return cls(
            configured,
            *actual.split(" "),
        )
