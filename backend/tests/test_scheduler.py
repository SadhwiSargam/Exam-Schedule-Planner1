import pytest
from datetime import date, timedelta
from scheduler.iat import schedule_iat, validate_iat_schedule
from scheduler.lab_internal import schedule_lab_internal, validate_lab_internal_schedule
from scheduler.lab_external import schedule_lab_external, validate_lab_external_schedule
from scheduler.see import schedule_see, validate_see_schedule
from scheduler.engine import SchedulingEngine, generate_schedule, validate_schedule
from scheduler.types import SubjectProtocol, ScheduleConfigProtocol
from scheduler.common import working_days_list


class MockSubject:
    def __init__(self, code, name, category, internal_count=3, internal_duration_minutes=90,
                 see_duration_minutes=180, lab_internal_duration_minutes=120,
                 lab_external_duration_minutes=180, mathematics_related=False, num_batches=1):
        self.code = code
        self.name = name
        self.category = category
        self.internal_count = internal_count
        self.internal_duration_minutes = internal_duration_minutes
        self.see_duration_minutes = see_duration_minutes
        self.lab_internal_duration_minutes = lab_internal_duration_minutes
        self.lab_external_duration_minutes = lab_external_duration_minutes
        self.mathematics_related = mathematics_related
        self.num_batches = num_batches


class MockConfig:
    def __init__(self, **kwargs):
        defaults = {
            'iat1_start': date(2024, 9, 15), 'iat1_end': date(2024, 9, 30),
            'iat2_start': date(2024, 10, 15), 'iat2_end': date(2024, 10, 31),
            'iat3_start': date(2024, 11, 15), 'iat3_end': date(2024, 11, 30),
            'iat_morning_start': '09:30', 'iat_morning_end': '11:00',
            'iat_afternoon_start': '14:30', 'iat_afternoon_end': '16:00',
            'lab_internal_start': date(2024, 12, 1), 'lab_internal_end': date(2024, 12, 15),
            'lab_external_start': date(2024, 12, 16), 'lab_external_end': date(2024, 12, 25),
            'max_lab_batches_per_day': 2,
            'see_start': date(2025, 1, 5), 'see_end': date(2025, 1, 25),
            'see_gap_days': 1,
            'weekend_exclude_saturday': True, 'weekend_exclude_sunday': True,
        }
        for k, v in {**defaults, **kwargs}.items():
            setattr(self, k, v)


def test_weekend_exclusion():
    """Test that weekends are excluded from working days."""
    start = date(2024, 9, 16)
    end = date(2024, 9, 20)
    holidays = set()
    days = working_days_list(start, end, holidays)
    assert date(2024, 9, 21) not in days
    assert date(2024, 9, 22) not in days


def test_holiday_exclusion():
    """Test that holidays are excluded from working days."""
    start = date(2024, 9, 16)
    end = date(2024, 9, 20)
    holidays = {date(2024, 9, 18)}
    days = working_days_list(start, end, holidays)
    assert date(2024, 9, 18) not in days


def test_iat_mathematics_first():
    """Test that mathematics-related subjects are scheduled first in IAT."""
    subjects = [
        MockSubject("CS101", "Programming", "theory", mathematics_related=False),
        MockSubject("MA101", "Mathematics", "theory", mathematics_related=True),
        MockSubject("CS102", "Data Structures", "theory", mathematics_related=False),
    ]
    start = date(2024, 9, 16)
    end = date(2024, 9, 20)
    holidays = set()
    schedule = schedule_iat(subjects, start, end, holidays, 1)
    assert schedule[0]["subject_code"] == "MA101"
    assert schedule[1]["subject_code"] == "CS101"
    assert schedule[2]["subject_code"] == "CS102"


def test_iat_subject_code_ordering():
    """Test that non-math subjects are ordered by subject code."""
    subjects = [
        MockSubject("CS102", "Data Structures", "theory"),
        MockSubject("CS101", "Programming", "theory"),
        MockSubject("EE101", "Electronics", "theory"),
    ]
    start = date(2024, 9, 16)
    end = date(2024, 9, 20)
    holidays = set()
    schedule = schedule_iat(subjects, start, end, holidays, 1)
    codes = [e["subject_code"] for e in schedule]
    assert codes == ["CS101", "CS102", "EE101"]


def test_iat_date_windows():
    """Test that IAT respects configured date windows."""
    subjects = [MockSubject("CS101", "Programming", "theory")]
    start = date(2024, 9, 16)
    end = date(2024, 9, 20)
    holidays = set()
    schedule = schedule_iat(subjects, start, end, holidays, 1)
    assert all(date.fromisoformat(e["date"]) >= start for e in schedule)
    assert all(date.fromisoformat(e["date"]) <= end for e in schedule)


def test_lab_internal_batches():
    """Test that lab internal schedules multiple batches correctly."""
    subjects = [MockSubject("CS101", "Programming Lab", "practical", num_batches=2)]
    start = date(2024, 12, 2)
    end = date(2024, 12, 10)
    holidays = set()
    schedule = schedule_lab_internal(subjects, start, end, holidays, max_batches_per_day=2)
    assert len(schedule) == 2
    batches = [e["batch_number"] for e in schedule]
    assert set(batches) == {1, 2}


def test_lab_external_eligibility():
    """Test that only practical subjects are eligible for lab external by default."""
    subjects = [
        MockSubject("CS101", "Programming", "theory"),
        MockSubject("CS102", "Programming Lab", "practical"),
        MockSubject("CS103", "OS", "both"),
    ]
    start = date(2024, 12, 16)
    end = date(2024, 12, 20)
    holidays = set()
    schedule = schedule_lab_external(subjects, start, end, holidays, include_both=False)
    assert len(schedule) == 1
    assert schedule[0]["subject_code"] == "CS102"


def test_lab_external_after_iat3():
    """Test that lab external is scheduled after IAT 3 end date."""
    subjects = [MockSubject("CS101", "Programming Lab", "practical", num_batches=1)]
    start = date(2024, 12, 1)
    end = date(2024, 12, 20)
    holidays = set()
    iat3_end = date(2024, 12, 10)
    schedule = schedule_lab_external(subjects, start, end, holidays, iat3_end_date=iat3_end)
    scheduled_date = date.fromisoformat(schedule[0]["date"])
    assert scheduled_date > iat3_end


def test_see_subject_eligibility():
    """Test that only theory and both subjects get SEE."""
    subjects = [
        MockSubject("CS101", "Programming", "theory"),
        MockSubject("CS102", "Programming Lab", "practical"),
        MockSubject("CS103", "OS", "both"),
    ]
    start = date(2025, 1, 6)
    end = date(2025, 1, 20)
    holidays = set()
    schedule = schedule_see(subjects, start, end, holidays)
    codes = [e["subject_code"] for e in schedule]
    assert "CS101" in codes
    assert "CS103" in codes
    assert "CS102" not in codes


def test_see_gap_rules():
    """Test that SEE has at least one day gap between exams."""
    subjects = [
        MockSubject("CS101", "Programming", "theory"),
        MockSubject("CS102", "Data Structures", "theory"),
        MockSubject("CS103", "Algorithms", "theory"),
    ]
    start = date(2025, 1, 6)
    end = date(2025, 1, 20)
    holidays = set()
    schedule = schedule_see(subjects, start, end, holidays, gap_days=1)
    dates = sorted([date.fromisoformat(e["date"]) for e in schedule])
    for i in range(1, len(dates)):
        diff = (dates[i] - dates[i-1]).days
        assert diff >= 2


def test_conflict_detection():
    """Test that conflict detection works."""
    schedule = [
        {"exam_type": "IAT 1", "subject_code": "CS101", "date": "2024-09-16", "start": "09:30", "end": "11:00", "batch_number": 1},
        {"exam_type": "IAT 1", "subject_code": "CS102", "date": "2024-09-16", "start": "09:30", "end": "11:00", "batch_number": 1},
    ]
    subjects = [
        MockSubject("CS101", "Programming", "theory"),
        MockSubject("CS102", "Data Structures", "theory"),
    ]
    config = MockConfig()
    engine = SchedulingEngine(config, set())
    conflicts = engine.validate_all(schedule, subjects)
    assert any("Time conflict" in c for c in conflicts)


def test_unscheduled_examinations():
    """Test that unscheduled exams are reported."""
    subjects = [MockSubject("CS101", "Programming", "theory")]
    config = MockConfig(iat1_start=None, iat1_end=None)
    engine = SchedulingEngine(config, set())
    entries, validation = engine.generate_full_schedule(subjects)
    assert any("not configured" in w for w in validation["warnings"])


def test_empty_subject_list():
    """Test scheduling with empty subject list."""
    subjects = []
    config = MockConfig()
    engine = SchedulingEngine(config, set())
    entries, validation = engine.generate_full_schedule(subjects)
    assert entries == []


def test_invalid_date_windows():
    """Test that invalid date windows are handled."""
    subjects = [MockSubject("CS101", "Programming", "theory")]
    config = MockConfig(iat1_start=date(2024, 9, 30), iat1_end=date(2024, 9, 15))
    engine = SchedulingEngine(config, set())
    entries, validation = engine.generate_full_schedule(subjects)
    assert len(validation["unscheduled"]) > 0


def test_full_schedule_generation():
    """Test complete schedule generation with all exam types."""
    subjects = [
        MockSubject("MA101", "Mathematics", "theory", mathematics_related=True),
        MockSubject("CS101", "Programming", "theory"),
        MockSubject("CS102", "Programming Lab", "practical", num_batches=2),
        MockSubject("CS103", "Operating Systems", "both"),
    ]
    config = MockConfig()
    engine = SchedulingEngine(config, {date(2024, 10, 2)})
    entries, validation = engine.generate_full_schedule(subjects)
    assert len(entries) > 0
    types = {e["exam_type"] for e in entries}
    assert "IAT 1" in types
    assert "IAT 2" in types
    assert "IAT 3" in types
    assert "Lab Internal" in types
    assert "Lab External" in types
    assert "SEE" in types


def test_validation_with_known_schedule():
    """Test validation of a known valid schedule."""
    subjects = [MockSubject("CS101", "Programming", "theory")]
    config = MockConfig(
        iat1_start=date(2024, 9, 16), iat1_end=date(2024, 9, 16),
        iat2_start=None, iat2_end=None,
        iat3_start=None, iat3_end=None,
        lab_internal_start=None, lab_internal_end=None,
        lab_external_start=None, lab_external_end=None,
        see_start=date(2025, 1, 6), see_end=date(2025, 1, 6),
    )
    schedule = [
        {"exam_type": "IAT 1", "subject_code": "CS101", "date": "2024-09-16", "start": "09:30", "end": "11:00", "batch_number": 1},
        {"exam_type": "SEE", "subject_code": "CS101", "date": "2025-01-06", "start": "09:30", "end": "12:30", "batch_number": 1},
    ]
    result = validate_schedule(schedule, subjects, config, [])
    assert result["valid"] is True
    assert result["conflicts"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])