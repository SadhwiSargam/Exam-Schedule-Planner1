from datetime import date, time
from typing import Protocol
from .common import (
    working_days_list,
    ordered_subjects,
    generate_time_slots,
    check_slot_capacity,
    parse_time,
    next_working_day,
)
from .types import SubjectProtocol


def get_lab_internal_subjects(subjects: list[SubjectProtocol]) -> list[SubjectProtocol]:
    """Filter subjects eligible for laboratory internal examinations."""
    return [s for s in subjects if s.category in ("practical", "both") and s.num_batches > 0]


def validate_no_theory_lab_internal(subjects: list[SubjectProtocol]) -> list[str]:
    """Validate that no theory subjects are scheduled for lab internal."""
    errors = []
    for s in subjects:
        if s.category == "theory" and s.num_batches > 0:
            errors.append(f"{s.code}: Theory subject cannot have lab internal batches")
    return errors


def schedule_lab_internal(
    subjects: list[SubjectProtocol],
    start_date: date,
    end_date: date,
    holidays: set[date],
    lab_internal_duration_minutes: int = 120,
    max_batches_per_day: int = 2,
    morning_start: str = "09:30",
    morning_end: str = "11:30",
    afternoon_start: str = "14:00",
    afternoon_end: str = "16:00",
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> list[dict]:
    """
    Schedule laboratory internal examinations.

    Returns list of scheduled entries.
    Raises ValueError if scheduling fails.
    """
    eligible = get_lab_internal_subjects(subjects)
    eligible = ordered_subjects(eligible)

    if not eligible:
        return []

    slot_times = [
        (parse_time(morning_start), parse_time(morning_end)),
        (parse_time(afternoon_start), parse_time(afternoon_end)),
    ]

    working = working_days_list(start_date, end_date, holidays, exclude_saturday, exclude_sunday)

    schedule = []
    day_index = 0

    for subject in eligible:
        batches_scheduled = 0
        while batches_scheduled < subject.num_batches and day_index < len(working):
            current_day = working[day_index]
            slots_today = 0

            for slot in slot_times:
                if batches_scheduled >= subject.num_batches:
                    break
                if slots_today >= max_batches_per_day:
                    break
                if not check_slot_capacity(lab_internal_duration_minutes, slot[0], slot[1]):
                    raise ValueError(
                        f"{subject.code}: lab internal duration ({lab_internal_duration_minutes}min) exceeds slot capacity."
                    )

                batch_num = batches_scheduled + 1
                schedule.append({
                    "exam_type": "Lab Internal",
                    "subject_code": subject.code,
                    "subject_name": subject.name,
                    "date": current_day.isoformat(),
                    "start": slot[0].strftime("%H:%M"),
                    "end": slot[1].strftime("%H:%M"),
                    "batch_number": batch_num,
                })
                batches_scheduled += 1
                slots_today += 1

            day_index += 1

        if batches_scheduled < subject.num_batches:
            raise ValueError(
                f"Not enough days to schedule all {subject.num_batches} batches for {subject.code} "
                f"({batches_scheduled} scheduled). Need more days in lab internal window."
            )

    return schedule


def validate_lab_internal_schedule(
    schedule: list[dict],
    subjects: list[SubjectProtocol],
    start_date: date,
    end_date: date,
    holidays: set[date],
    max_batches_per_day: int = 2,
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
) -> list[str]:
    """Validate a lab internal schedule and return list of conflicts/warnings."""
    errors = []
    eligible = get_lab_internal_subjects(subjects)

    subject_batches = {s.code: s.num_batches for s in eligible}
    scheduled_counts = {}

    for entry in schedule:
        code = entry["subject_code"]
        entry_date = date.fromisoformat(entry["date"])

        if entry_date < start_date or entry_date > end_date:
            errors.append(f"{code}: lab internal date {entry['date']} outside configured window")
        if entry_date in holidays:
            errors.append(f"{code}: lab internal scheduled on holiday {entry['date']}")
        if exclude_saturday and entry_date.weekday() == 5:
            errors.append(f"{code}: lab internal scheduled on Saturday")
        if exclude_sunday and entry_date.weekday() == 6:
            errors.append(f"{code}: lab internal scheduled on Sunday")

        key = (code, entry_date)
        scheduled_counts[key] = scheduled_counts.get(key, 0) + 1

        if scheduled_counts[key] > max_batches_per_day:
            errors.append(f"{code}: more than {max_batches_per_day} batches on {entry['date']}")

    for code, expected in subject_batches.items():
        actual = sum(1 for e in schedule if e["subject_code"] == code)
        if actual != expected:
            errors.append(f"{code}: expected {expected} lab internal batches, got {actual}")

    seen = set()
    for entry in schedule:
        key = (entry["subject_code"], entry["batch_number"], entry["date"], entry["start"])
        if key in seen:
            errors.append(f"Duplicate lab internal: {entry['subject_code']} batch {entry['batch_number']} on {entry['date']} at {entry['start']}")
        seen.add(key)

    return errors