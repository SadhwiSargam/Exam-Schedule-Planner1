from datetime import date, time, timedelta
from typing import Protocol
from .common import (
    working_days_list,
    ordered_subjects,
    parse_time,
    check_slot_capacity,
    next_working_day,
)
from .types import SubjectProtocol


def get_see_subjects(subjects: list[SubjectProtocol]) -> list[SubjectProtocol]:
    """Filter subjects eligible for SEE examinations."""
    return [s for s in subjects if s.category in ("theory", "both")]


def schedule_see(
    subjects: list[SubjectProtocol],
    start_date: date,
    end_date: date,
    holidays: set[date],
    see_duration_minutes: int = 180,
    gap_days: int = 1,
    morning_start: str = "09:30",
    morning_end: str = "12:30",
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> list[dict]:
    """
    Schedule SEE examinations.

    One SEE per day with at least gap_days between exams.
    Returns list of scheduled entries.
    Raises ValueError if scheduling fails.
    """
    eligible = get_see_subjects(subjects)
    eligible = ordered_subjects(eligible)

    if not eligible:
        return []

    working = working_days_list(start_date, end_date, holidays, exclude_saturday, exclude_sunday)

    schedule = []
    day_index = 0

    for subject in eligible:
        while day_index < len(working):
            current_day = working[day_index]

            slot_start = parse_time(morning_start)
            slot_end = parse_time(morning_end)

            if not check_slot_capacity(see_duration_minutes, slot_start, slot_end):
                raise ValueError(
                    f"{subject.code}: SEE duration ({see_duration_minutes}min) exceeds slot capacity."
                )

            schedule.append({
                "exam_type": "SEE",
                "subject_code": subject.code,
                "subject_name": subject.name,
                "date": current_day.isoformat(),
                "start": slot_start.strftime("%H:%M"),
                "end": slot_end.strftime("%H:%M"),
                "batch_number": 1,
            })

            day_index += gap_days + 1
            break
        else:
            raise ValueError(
                f"Not enough working days to schedule SEE for {subject.code} "
                f"with {gap_days} day gap requirement."
            )

    return schedule


def validate_see_schedule(
    schedule: list[dict],
    subjects: list[SubjectProtocol],
    start_date: date,
    end_date: date,
    holidays: set[date],
    gap_days: int = 1,
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> list[str]:
    """Validate a SEE schedule and return list of conflicts/warnings."""
    errors = []
    eligible = get_see_subjects(subjects)

    subject_codes = {s.code for s in eligible}

    for entry in schedule:
        code = entry["subject_code"]
        entry_date = date.fromisoformat(entry["date"])

        if code not in subject_codes:
            errors.append(f"{code}: not eligible for SEE (category: practical)")

        if entry_date < start_date or entry_date > end_date:
            errors.append(f"{code}: SEE date {entry['date']} outside configured window")
        if entry_date in holidays:
            errors.append(f"{code}: SEE scheduled on holiday {entry['date']}")
        if exclude_saturday and entry_date.weekday() == 5:
            errors.append(f"{code}: SEE scheduled on Saturday")
        if exclude_sunday and entry_date.weekday() == 6:
            errors.append(f"{code}: SEE scheduled on Sunday")

    seen_dates = set()
    for entry in schedule:
        if entry["date"] in seen_dates:
            errors.append(f"Multiple SEE exams on same day: {entry['date']}")
        seen_dates.add(entry["date"])

    sorted_dates = sorted([date.fromisoformat(e["date"]) for e in schedule])
    for i in range(1, len(sorted_dates)):
        diff = (sorted_dates[i] - sorted_dates[i - 1]).days
        if diff <= gap_days:
            errors.append(f"SEE gap violation: only {diff} days between {sorted_dates[i-1]} and {sorted_dates[i]} (need {gap_days+1})")

    for code in subject_codes:
        if not any(e["subject_code"] == code for e in schedule):
            errors.append(f"{code}: missing SEE examination")

    seen = set()
    for entry in schedule:
        key = (entry["subject_code"], entry["date"], entry["start"])
        if key in seen:
            errors.append(f"Duplicate SEE: {entry['subject_code']} on {entry['date']} at {entry['start']}")
        seen.add(key)

    return errors