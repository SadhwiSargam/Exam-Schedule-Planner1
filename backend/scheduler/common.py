from datetime import date, time, datetime, timedelta
from typing import Generator, Optional


def parse_time(time_str: str) -> time:
    """Parse HH:MM time string to time object."""
    return datetime.strptime(time_str, "%H:%M").time()


def time_to_minutes(t: time) -> int:
    """Convert time to minutes since midnight."""
    return t.hour * 60 + t.minute


def minutes_to_time(minutes: int) -> time:
    """Convert minutes since midnight to time object."""
    return time(minutes // 60, minutes % 60)


def add_minutes(t: time, minutes: int) -> time:
    """Add minutes to a time."""
    return minutes_to_time(time_to_minutes(t) + minutes)


def slot_duration_minutes(start: time, end: time) -> int:
    """Calculate duration of a time slot in minutes."""
    return time_to_minutes(end) - time_to_minutes(start)


def working_days(
    start: date,
    end: date,
    holidays: set[date],
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> Generator[date, None, None]:
    """Yield working days between start and end (inclusive), excluding holidays and weekends."""
    day = start
    while day <= end:
        is_weekend = (day.weekday() == 5 and exclude_saturday) or (day.weekday() == 6 and exclude_sunday)
        if not is_weekend and day not in holidays:
            yield day
        day += timedelta(days=1)


def working_days_list(
    start: date,
    end: date,
    holidays: set[date],
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> list[date]:
    """Return list of working days."""
    return list(working_days(start, end, holidays, exclude_saturday, exclude_sunday))


def is_working_day(
    day: date,
    holidays: set[date],
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> bool:
    """Check if a given day is a working day."""
    is_weekend = (day.weekday() == 5 and exclude_saturday) or (day.weekday() == 6 and exclude_sunday)
    return not is_weekend and day not in holidays


def next_working_day(
    day: date,
    holidays: set[date],
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> date:
    """Get the next working day after the given day."""
    next_day = day + timedelta(days=1)
    while not is_working_day(next_day, holidays, exclude_saturday, exclude_sunday):
        next_day += timedelta(days=1)
    return next_day


def previous_working_day(
    day: date,
    holidays: set[date],
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> date:
    """Get the previous working day before the given day."""
    prev_day = day - timedelta(days=1)
    while not is_working_day(prev_day, holidays, exclude_saturday, exclude_sunday):
        prev_day -= timedelta(days=1)
    return prev_day


def ordered_subjects(subjects: list) -> list:
    """Order subjects: mathematics-related first, then by subject code."""
    math_subjects = [s for s in subjects if s.mathematics_related]
    other = sorted([s for s in subjects if not s.mathematics_related], key=lambda s: s.code.casefold())
    return math_subjects + other


def generate_time_slots(
    start_date: date,
    end_date: date,
    slot_times: list[tuple[time, time]],
    holidays: set[date],
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> list[tuple[date, tuple[time, time]]]:
    """Generate all available time slots in the date range."""
    slots = []
    for day in working_days(start_date, end_date, holidays, exclude_saturday, exclude_sunday):
        for slot in slot_times:
            slots.append((day, slot))
    return slots


def check_slot_capacity(subject_duration: int, slot_start: time, slot_end: time) -> bool:
    """Check if subject duration fits in the time slot."""
    return subject_duration <= slot_duration_minutes(slot_start, slot_end)