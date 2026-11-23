from datetime import date
from typing import Optional
from schemas import Subject
from .engine import generate_schedule, validate_schedule
from .common import parse_time
from .iat import schedule_iat


def generate_iat(
    subjects: list[Subject],
    start_date: date,
    end_date: date,
    holidays: set[date],
    iat_number: int,
    morning_start: str = "09:30",
    morning_end: str = "11:00",
    afternoon_start: str = "14:30",
    afternoon_end: str = "16:00",
) -> list[dict]:
    """Legacy IAT generation for backward compatibility."""
    return schedule_iat(
        subjects, start_date, end_date, holidays, iat_number,
        morning_start, morning_end, afternoon_start, afternoon_end
    )


def generate_full_schedule(
    subjects: list[Subject],
    config: dict,
    holidays: list[date],
) -> tuple[list[dict], dict]:
    """Generate full schedule using engine."""
    from schemas import ScheduleConfigBase
    cfg = ScheduleConfigBase(**config)
    return generate_schedule(subjects, cfg, holidays)


def validate_full_schedule(
    entries: list[dict],
    subjects: list[Subject],
    config: dict,
    holidays: list[date],
) -> dict:
    """Validate full schedule using engine."""
    from schemas import ScheduleConfigBase
    cfg = ScheduleConfigBase(**config)
    return validate_schedule(entries, subjects, cfg, holidays)