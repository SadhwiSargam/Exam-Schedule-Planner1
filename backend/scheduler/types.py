from datetime import date
from typing import Protocol


class SubjectProtocol(Protocol):
    code: str
    name: str
    category: str
    internal_count: int
    internal_duration_minutes: int
    see_duration_minutes: int
    lab_internal_duration_minutes: int
    lab_external_duration_minutes: int
    mathematics_related: bool
    num_batches: int


class ScheduleConfigProtocol(Protocol):
    iat1_start: date | None
    iat1_end: date | None
    iat2_start: date | None
    iat2_end: date | None
    iat3_start: date | None
    iat3_end: date | None

    iat_morning_start: str
    iat_morning_end: str
    iat_afternoon_start: str
    iat_afternoon_end: str

    lab_internal_start: date | None
    lab_internal_end: date | None
    lab_external_start: date | None
    lab_external_end: date | None
    max_lab_batches_per_day: int

    see_start: date | None
    see_end: date | None
    see_gap_days: int

    weekend_exclude_saturday: bool
    weekend_exclude_sunday: bool