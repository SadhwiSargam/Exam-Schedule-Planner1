from datetime import date, time
from typing import Protocol
from .common import (
    working_days_list,
    ordered_subjects,
    generate_time_slots,
    check_slot_capacity,
    parse_time,
)
from .types import SubjectProtocol


def get_iat_subjects(subjects: list[SubjectProtocol], iat_number: int) -> list[SubjectProtocol]:
    """Filter subjects eligible for the given IAT number."""
    return [
        s for s in subjects
        if s.category in ("theory", "both") and s.internal_count >= iat_number
    ]


def schedule_iat(
    subjects: list[SubjectProtocol],
    start_date: date,
    end_date: date,
    holidays: set[date],
    iat_number: int,
    morning_start: str = "09:30",
    morning_end: str = "11:00",
    afternoon_start: str = "14:30",
    afternoon_end: str = "16:00",
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> list[dict]:
    """
    Schedule IAT examinations.

    Returns list of scheduled entries with: subject_code, subject_name, date, start, end, exam_type
    Raises ValueError if scheduling fails.
    """
    eligible = get_iat_subjects(subjects, iat_number)
    eligible = ordered_subjects(eligible)

    if not eligible:
        return []

    slot_times = [
        (parse_time(morning_start), parse_time(morning_end)),
        (parse_time(afternoon_start), parse_time(afternoon_end)),
    ]

    slots = generate_time_slots(
        start_date, end_date, slot_times, holidays, exclude_saturday, exclude_sunday
    )

    if len(eligible) > len(slots):
        raise ValueError(
            f"Not enough slots for IAT {iat_number}: {len(slots)} available for {len(eligible)} subjects."
        )

    schedule = []
    for index, subject in enumerate(eligible):
        day, slot = slots[index]
        if not check_slot_capacity(subject.internal_duration_minutes, slot[0], slot[1]):
            raise ValueError(
                f"{subject.code}: exam duration ({subject.internal_duration_minutes}min) exceeds slot capacity."
            )
        schedule.append({
            "exam_type": f"IAT {iat_number}",
            "subject_code": subject.code,
            "subject_name": subject.name,
            "date": day.isoformat(),
            "start": slot[0].strftime("%H:%M"),
            "end": slot[1].strftime("%H:%M"),
            "batch_number": 1,
        })

    return schedule


def validate_iat_schedule(
    schedule: list[dict],
    subjects: list[SubjectProtocol],
    start_date: date,
    end_date: date,
    holidays: set[date],
    iat_number: int,
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> list[str]:
    """Validate an IAT schedule and return list of conflicts/warnings."""
    errors = []
    eligible = get_iat_subjects(subjects, iat_number)
    eligible = ordered_subjects(eligible)

    if len(schedule) != len(eligible):
        errors.append(f"IAT {iat_number}: expected {len(eligible)} entries, got {len(schedule)}")

    seen = set()
    for entry in schedule:
        key = (entry["subject_code"], entry["date"], entry["start"])
        if key in seen:
            errors.append(f"Duplicate entry: {entry['subject_code']} on {entry['date']} at {entry['start']}")
        seen.add(key)

        entry_date = date.fromisoformat(entry["date"])
        if entry_date < start_date or entry_date > end_date:
            errors.append(f"{entry['subject_code']}: date {entry['date']} outside IAT {iat_number} window")

        if entry_date in holidays:
            errors.append(f"{entry['subject_code']}: scheduled on holiday {entry['date']}")

        if exclude_saturday and entry_date.weekday() == 5:
            errors.append(f"{entry['subject_code']}: scheduled on Saturday")
        if exclude_sunday and entry_date.weekday() == 6:
            errors.append(f"{entry['subject_code']}: scheduled on Sunday")

    return errors