from datetime import date, time, timedelta
from typing import Protocol
from .common import (
    working_days_list,
    ordered_subjects,
    generate_time_slots,
    check_slot_capacity,
    parse_time,
)
from .types import SubjectProtocol


def get_lab_external_subjects(subjects: list[SubjectProtocol], include_both: bool = False) -> list[SubjectProtocol]:
    """Filter subjects eligible for laboratory external examinations.

    By default, only 'practical' category subjects are eligible.
    If include_both is True, 'both' category subjects are also included.
    """
    if include_both:
        return [s for s in subjects if s.category in ("practical", "both") and s.num_batches > 0]
    return [s for s in subjects if s.category == "practical" and s.num_batches > 0]


def validate_no_theory_lab_external(subjects: list[SubjectProtocol]) -> list[str]:
    """Validate that no theory subjects are scheduled for lab external."""
    errors = []
    for s in subjects:
        if s.category == "theory" and s.num_batches > 0:
            errors.append(f"{s.code}: Theory subject cannot have lab external batches")
    return errors


def schedule_lab_external(
    subjects: list[SubjectProtocol],
    start_date: date,
    end_date: date,
    holidays: set[date],
    iat3_end_date: date | None = None,
    lab_external_duration_minutes: int = 180,
    max_batches_per_day: int = 2,
    morning_start: str = "09:00",
    morning_end: str = "12:00",
    afternoon_start: str = "13:00",
    afternoon_end: str = "16:00",
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
    include_both: bool = False,
) -> list[dict]:
    """
    Schedule laboratory external examinations.

    Must be scheduled after IAT 3 (iat3_end_date).
    Returns list of scheduled entries.
    Raises ValueError if scheduling fails.
    """
    eligible = get_lab_external_subjects(subjects, include_both)
    eligible = ordered_subjects(eligible)

    if not eligible:
        return []

    actual_start = start_date
    if iat3_end_date and iat3_end_date > start_date:
        actual_start = iat3_end_date + timedelta(days=1)

    slot_times = [
        (parse_time(morning_start), parse_time(morning_end)),
        (parse_time(afternoon_start), parse_time(afternoon_end)),
    ]

    working = working_days_list(actual_start, end_date, holidays, exclude_saturday, exclude_sunday)

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
                if not check_slot_capacity(lab_external_duration_minutes, slot[0], slot[1]):
                    raise ValueError(
                        f"{subject.code}: lab external duration ({lab_external_duration_minutes}min) exceeds slot capacity."
                    )

                batch_num = batches_scheduled + 1
                schedule.append({
                    "exam_type": "Lab External",
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
                f"({batches_scheduled} scheduled). Need more days in lab external window."
            )

    return schedule


def validate_lab_external_schedule(
    schedule: list[dict],
    subjects: list[SubjectProtocol],
    start_date: date,
    end_date: date,
    holidays: set[date],
    iat3_end_date: date | None = None,
    max_batches_per_day: int = 2,
    exclude_saturday: bool = True,
    exclude_sunday: bool = True,
    include_both: bool = False,
) -> list[str]:
    """Validate a lab external schedule and return list of conflicts/warnings."""
    errors = []
    eligible = get_lab_external_subjects(subjects, include_both)

    subject_batches = {s.code: s.num_batches for s in eligible}
    scheduled_counts = {}

    actual_start = start_date
    if iat3_end_date and iat3_end_date > start_date:
        actual_start = iat3_end_date + timedelta(days=1)

    for entry in schedule:
        code = entry["subject_code"]
        entry_date = date.fromisoformat(entry["date"])

        if entry_date < actual_start:
            errors.append(f"{code}: lab external scheduled before IAT 3 end ({iat3_end_date})")
        if entry_date > end_date:
            errors.append(f"{code}: lab external date {entry['date']} outside configured window")
        if entry_date in holidays:
            errors.append(f"{code}: lab external scheduled on holiday {entry['date']}")
        if exclude_saturday and entry_date.weekday() == 5:
            errors.append(f"{code}: lab external scheduled on Saturday")
        if exclude_sunday and entry_date.weekday() == 6:
            errors.append(f"{code}: lab external scheduled on Sunday")

        key = (code, entry_date)
        scheduled_counts[key] = scheduled_counts.get(key, 0) + 1

        if scheduled_counts[key] > max_batches_per_day:
            errors.append(f"{code}: more than {max_batches_per_day} lab external batches on {entry['date']}")

    for code, expected in subject_batches.items():
        actual = sum(1 for e in schedule if e["subject_code"] == code)
        if actual != expected:
            errors.append(f"{code}: expected {expected} lab external batches, got {actual}")

    seen = set()
    for entry in schedule:
        key = (entry["subject_code"], entry["batch_number"], entry["date"], entry["start"])
        if key in seen:
            errors.append(f"Duplicate lab external: {entry['subject_code']} batch {entry['batch_number']} on {entry['date']} at {entry['start']}")
        seen.add(key)

    return errors